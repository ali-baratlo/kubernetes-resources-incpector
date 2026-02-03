import json
from kubernetes import client
from kubernetes.client import ApiClient, ApiException
from cluster_config import CLUSTERS
from utils.db import get_resource_collection, get_audit_log_collection
from utils.logger import logger
from models.resource import Resource, AuditLog
from jsondiff import diff
import urllib3

# `namespaced=True` for resources within a namespace.
# `namespaced=False` for cluster-wide resources.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

RESOURCE_TYPES = [
    #{"name": "Pod", "list_func": "list_namespaced_pod", "api": "CoreV1Api", "namespaced": True},
    {"name": "ConfigMap", "list_func": "list_namespaced_config_map", "api": "CoreV1Api", "namespaced": True},
    {"name": "Service", "list_func": "list_namespaced_service", "api": "CoreV1Api", "namespaced": True},
    {"name": "PersistentVolumeClaim", "list_func": "list_namespaced_persistent_volume_claim", "api": "CoreV1Api", "namespaced": True},
    {"name": "Deployment", "list_func": "list_namespaced_deployment", "api": "AppsV1Api", "namespaced": True},
    {"name": "StatefulSet", "list_func": "list_namespaced_stateful_set", "api": "AppsV1Api", "namespaced": True},
    {"name": "DaemonSet", "list_func": "list_namespaced_daemon_set", "api": "AppsV1Api", "namespaced": True},
    {"name": "Job", "list_func": "list_namespaced_job", "api": "BatchV1Api", "namespaced": True},
    {"name": "CronJob", "list_func": "list_namespaced_cron_job", "api": "BatchV1Api", "namespaced": True},
    {"name": "Ingress", "list_func": "list_namespaced_ingress", "api": "NetworkingV1Api", "namespaced": True},
    {"name": "NetworkPolicy", "list_func": "list_namespaced_network_policy", "api": "NetworkingV1Api", "namespaced": True},
    {"name": "HorizontalPodAutoscaler", "list_func": "list_namespaced_horizontal_pod_autoscaler", "api": "AutoscalingV1Api", "namespaced": True},
    {"name": "PersistentVolume", "list_func": "list_persistent_volume", "api": "CoreV1Api", "namespaced": False},
    #{"name": "CustomResourceDefinition", "list_func": "list_custom_resource_definition", "api": "ApiextensionsV1Api", "namespaced": False},
]

def _process_and_store_resources(items, cluster_name, resource_type, namespace, namespace_labels, collection, audit_collection, api_client):
    """Helper function to process a list of resource items and store them."""
    #environment = "production" if namespace and "prod" in namespace else "non-production"
    environment = "non-production"
    if namespace_labels and namespace_labels.get("environment") == "production":
        environment = "production"
    for item in items:
        resource_dict = api_client.sanitize_for_serialization(item)
        full_resource_str = json.dumps(resource_dict)

        query = {
            "cluster_name": cluster_name,
            "resource_type": resource_type,
            "resource_name": item.metadata.name,
        }
        if namespace:
            query["namespace"] = namespace

        existing_resource = collection.find_one(query)

        if existing_resource:
            if existing_resource["resource_version"] != item.metadata.resource_version:
                serializable_diff = diff(existing_resource["data"], resource_dict, syntax='symmetric', marshal=True)
                audit_log = AuditLog(
                    resource_id=str(existing_resource["_id"]),
                    old_version=existing_resource["resource_version"],
                    new_version=item.metadata.resource_version,
                    diff=serializable_diff,
                )
                audit_collection.insert_one(audit_log.model_dump())

                collection.update_one(
                    {"_id": existing_resource["_id"]},
                    {"$set": {
                        "resource_version": item.metadata.resource_version,
                        "data": resource_dict,
                        "full_resource_string": full_resource_str,
                        "created_at": audit_log.changed_at,
                        "environment": environment
                    }}
                )
                logger.info(f"Updated {resource_type} '{item.metadata.name}'" + (f" in '{namespace}'" if namespace else ""))
        else:
            new_resource = Resource(
                cluster_name=cluster_name,
                namespace=namespace or "",
                environment=environment,
                resource_type=resource_type,
                resource_name=item.metadata.name,
                resource_version=item.metadata.resource_version,
                data=resource_dict,
                full_resource_string=full_resource_str,
            )
            collection.insert_one(new_resource.model_dump())
            logger.info(f"Inserted new {resource_type} '{item.metadata.name}'" + (f" in '{namespace}'" if namespace else ""))

def collect_resources():
    """Collects various Kubernetes resources from configured clusters and stores them in MongoDB."""
    logger.info("Starting resource collection cycle...")
    resource_collection = get_resource_collection()
    audit_log_collection = get_audit_log_collection()
    api_client = ApiClient()

    for cluster in CLUSTERS:
        cluster_name = cluster["name"]
        logger.info(f"Starting collection for cluster: {cluster_name}")

        configuration = client.Configuration()
        configuration.host = cluster["api_server"]
        configuration.verify_ssl = False
        configuration.api_key = {"authorization": f"Bearer {cluster['token']}"}

        api_map = {
            "CoreV1Api": client.CoreV1Api(client.ApiClient(configuration)),
            "AppsV1Api": client.AppsV1Api(client.ApiClient(configuration)),
            "BatchV1Api": client.BatchV1Api(client.ApiClient(configuration)),
            "NetworkingV1Api": client.NetworkingV1Api(client.ApiClient(configuration)),
            "AutoscalingV1Api": client.AutoscalingV1Api(client.ApiClient(configuration)),
            "ApiextensionsV1Api": client.ApiextensionsV1Api(client.ApiClient(configuration)),
        }

        # Handle cluster-scoped resources
        logger.info(f"Processing cluster-scoped resources for {cluster_name}...")
        for res_type in filter(lambda r: not r["namespaced"], RESOURCE_TYPES):
            try:
                api_instance = api_map[res_type["api"]]
                list_func = getattr(api_instance, res_type["list_func"])
                resources = list_func()
                logger.info(f"Found {len(resources.items)} {res_type['name']} resources in {cluster_name}.")
                #_process_and_store_resources(resources.items, cluster_name, res_type["name"], None, resource_collection, audit_log_collection, api_client)
                _process_and_store_resources(resources.items, cluster_name, res_type["name"], None, None, resource_collection, audit_log_collection, api_client)
            except ApiException as e:
                logger.error(f"Error fetching {res_type['name']} from {cluster_name}: {e.reason}", exc_info=True)
            except Exception as e:
                logger.error(f"An unexpected error occurred fetching {res_type['name']}: {e}", exc_info=True)

        # Handle namespaced resources
        try:
            namespace_label_selector = cluster.get("namespace_label_selector", "")
            logger.info(f"Fetching namespaces from {cluster_name} with selector: '{namespace_label_selector or 'None'}'")
            namespaces = api_map["CoreV1Api"].list_namespace(label_selector=namespace_label_selector)
            logger.info(f"Found {len(namespaces.items)} namespaces to scan.")
        except ApiException as e:
            logger.error(f"Error fetching namespaces from {cluster_name}: {e.reason}", exc_info=True)
            continue

        for ns in namespaces.items:
            namespace_name = ns.metadata.name
            
            _process_and_store_resources([ns], cluster_name, "Namespace", None, ns.metadata.labels, resource_collection, audit_log_collection, api_client)
            
            logger.debug(f"Scanning namespace: {namespace_name}")
            for res_type in filter(lambda r: r["namespaced"], RESOURCE_TYPES):
                try:
                    api_instance = api_map[res_type["api"]]
                    list_func = getattr(api_instance, res_type["list_func"])
                    resources = list_func(namespace=namespace_name)
                    if resources.items:
                        logger.debug(f"Found {len(resources.items)} {res_type['name']} resources in {namespace_name}.")
                    #_process_and_store_resources(resources.items, cluster_name, res_type["name"], namespace_name, resource_collection, audit_log_collection, api_client)
                    _process_and_store_resources(resources.items, cluster_name, res_type["name"], namespace_name, ns.metadata.labels, resource_collection, audit_log_collection, api_client)
                except ApiException as e:
                    # Log 403 (Forbidden) as a warning, others as errors
                    if e.status == 403:
                        logger.warning(f"Permission denied fetching {res_type['name']} from {namespace_name}: {e.reason}")
                    else:
                        logger.error(f"API Error fetching {res_type['name']} from {namespace_name}: {e.reason}", exc_info=True)
                except Exception as e:
                    logger.error(f"An unexpected error occurred fetching {res_type['name']} in {namespace_name}: {e}", exc_info=True)

    logger.info("Resource collection cycle complete.")
