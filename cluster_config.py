import os
import yaml
from pathlib import Path

# Path where ConfigMap with cluster definitions is mounted
CLUSTERS_CONFIG_PATH = os.environ.get(
    "CLUSTERS_CONFIG_PATH",
    "/etc/odin/clusters.yaml"  # Default to local file for easier development
)

def load_clusters():
    """
    Loads cluster definitions from a YAML file and injects tokens and FQDNs
    from environment variables.
    Returns:
        list of dicts: Each dict contains cluster configuration.
    """
    try:
        with open(CLUSTERS_CONFIG_PATH, 'r') as f:
            clusters = yaml.safe_load(f)
    except FileNotFoundError:
        # In a real deployment, this should probably be a hard failure.
        # For development, we can return an empty list.
        print(f"Warning: Cluster config file not found at {CLUSTERS_CONFIG_PATH}. No clusters will be loaded.")
        return []

    if isinstance(clusters, dict):
        clusters = clusters.get("clusters", [])

    if not isinstance(clusters, list):
        raise ValueError(f"Invalid cluster config format in {CLUSTERS_CONFIG_PATH}")

    for cluster in clusters:
        # Handle required token
        token_env = cluster.get("token_env")
        if not token_env:
            raise ValueError(f"Cluster {cluster.get('name')} is missing 'token_env' field")
        cluster["token"] = os.environ.get(token_env).strip().strip('"')
        if not cluster["token"]:
            raise RuntimeError(f"Token for {token_env} not found in environment variables")

        # Handle optional FQDN
        fqdn_env = cluster.get("fqdn_env")
        if fqdn_env:
            cluster["fqdn"] = os.environ.get(fqdn_env)
        else:
            cluster["fqdn"] = None # Ensure the key exists

    return clusters

# This is the variable your other code imports
CLUSTERS = load_clusters()