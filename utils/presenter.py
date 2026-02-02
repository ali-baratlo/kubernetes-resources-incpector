def get_structured_data(resource: dict) -> dict:
    """
    Parses a resource dictionary and returns a structured summary.
    """
    resource_type = resource.get("resource_type", "").lower()
    data = resource.get("data", {})

    if not data:
        return {"Error": "No data available for this resource."}

    presenter_functions = {
        "deployment": present_deployment,
        "service": present_service,
        "secret": present_secret,
        "ingress": present_ingress,
        "configmap": present_configmap,
    }

    presenter_func = presenter_functions.get(resource_type)
    if presenter_func:
        return presenter_func(data)

    return {"Info": "Standard presentation for this resource type."}

def present_deployment(data: dict) -> dict:
    """Presents a summary of a Deployment."""
    spec = data.get("spec", {})
    status = data.get("status", {})
    template_spec = spec.get("template", {}).get("spec", {})

    containers = template_spec.get("containers", [])
    container_info = [
        {
            "Image": c.get("image"),
            "Ports": [p.get("containerPort") for p in c.get("ports", [])],
        }
        for c in containers
    ]

    return {
        "Replicas": spec.get("replicas"),
        "Available Replicas": status.get("availableReplicas"),
        "Ready Replicas": status.get("readyReplicas"),
        "Strategy": spec.get("strategy", {}).get("type"),
        "Containers": container_info,
    }

def present_service(data: dict) -> dict:
    """Presents a summary of a Service."""
    spec = data.get("spec", {})
    return {
        "Type": spec.get("type"),
        "Cluster IP": spec.get("clusterIP"),
        "Ports": [
            f"{p.get('port')}/{p.get('protocol')} -> {p.get('targetPort')}"
            for p in spec.get("ports", [])
        ],
        "Selector": spec.get("selector"),
    }

def present_secret(data: dict) -> dict:
    """Presents a summary of a Secret."""
    return {
        "Type": data.get("type"),
        "Data Keys": list(data.get("data", {}).keys()),
    }

def present_ingress(data: dict) -> dict:
    """Presents a summary of an Ingress."""
    spec = data.get("spec", {})
    rules = spec.get("rules", [])

    rule_info = [
        {
            "Host": r.get("host"),
            "Paths": [
                f"{p.get('path', '/')} -> {p.get('backend', {}).get('service', {}).get('name')}:{p.get('backend', {}).get('service', {}).get('port', {}).get('number')}"
                for p in r.get("http", {}).get("paths", [])
            ],
        }
        for r in rules
    ]

    return {
        "Ingress Class": spec.get("ingressClassName"),
        "Rules": rule_info,
    }

def present_configmap(data: dict) -> dict:
    """Presents a summary of a ConfigMap."""
    return data.get("data", {})