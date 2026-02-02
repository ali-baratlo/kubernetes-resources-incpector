# Odin - Kubernetes Resource Collector and Inspector

Odin is a powerful, containerized application designed to collect, store, and inspect Kubernetes resources from multiple clusters. It features a modern React frontend and a robust FastAPI backend, providing an interactive and user-friendly experience for searching and analyzing resource configurations.

![Project Screenshot](image/image_demo.png)

## Key Features

- **Modern React Frontend**: A fast, responsive, and intuitive user interface built with React and Vite.
- **Multi-Cluster Support**: Collects resources from any number of Kubernetes or OKD clusters.
- **Comprehensive Resource Collection**: Gathers a wide range of resources, including Pods, ConfigMaps, Secrets, Services, Deployments, StatefulSets, DaemonSets, Jobs, CronJobs, Ingresses, NetworkPolicies, PersistentVolumes (PVs), PersistentVolumeClaims (PVCs), HorizontalPodAutoscalers (HPAs), and CustomResourceDefinitions (CRDs).
- **MongoDB Backend**: Stores all resources as structured JSON documents, enabling flexible and powerful queries.
- **Resource Versioning & Auditing**: Tracks changes to resources over time by storing new versions and logging the differences.
- **RESTful API**: A robust FastAPI-powered API for all data operations.
- **Configurable Scheduled Data Collection**: A background job runs periodically to keep the resource data up-to-date. The interval is configurable via an environment variable.
- **Helm Ready**: Comes with a production-ready Helm chart .
- **Robust Logging and Startup**: Features detailed structured logging for easy debugging and a fail-fast mechanism that prevents the app from starting without a valid database connection.

## Technology Stack

- **Frontend**: React, Vite, Axios
- **Backend**: Python 3, FastAPI, Loguru
- **Database**: MongoDB
- **Deployment**: Docker, Docker Compose, Helm

---

## Deployment

There are two primary ways to deploy and run Odin: locally with Docker Compose for development and testing, or with the provided Helm chart for a production-grade Kubernetes deployment.

### 1. Local Development (with Docker Compose)

This method is ideal for local development and testing.

#### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

#### Setup
1.  **Configure Clusters:** Create a `clusters.yaml` file in the root of the project to define the clusters you want to monitor.
    ```yaml
    # clusters.yaml
    - name: my-cluster-1
      api_server: https://api.my-cluster-1.com:6443
      token_env: MY_CLUSTER_1_TOKEN
      namespace_label_selector: "environment=production" # Optional
      fqdn_env: MY_CLUSTER_1_FQDN # Optional: For generating clickable links
    ```

2.  **Set Environment Variables:** Create a `.env` file in the root directory for your cluster tokens and other configurations.
    ```env
    # .env
    MY_CLUSTER_1_TOKEN="your-kube-api-token-for-cluster-1"
    MY_CLUSTER_1_FQDN="console.apps.my-cluster-1.com" # Optional
    SCHEDULER_INTERVAL_HOURS=2 # Optional: Defaults to 1
    ```

3.  **Build and Run:**
    ```bash
    docker compose up --build
    ```
    The application will be available at `http://localhost:8000`.

---

### 2. Production Deployment (with Helm)

The provided Helm chart is the recommended way to deploy Odin to a production Kubernetes cluster.

#### Prerequisites
- [Helm](https://helm.sh/docs/intro/install/)
- A running Kubernetes cluster
- `kubectl` configured to connect to your cluster

#### Helm Chart Configuration
All configuration is managed in the `helm/values.yaml` file. Before deploying, you should customize this file to match your environment.

**Key values to configure:**
- `image.repository`: The URL of the Docker image repository where your Odin image is stored.
- `env.tokens`: A map of environment variable names to the **base64-encoded** tokens for your clusters.
- `env.fqdns`: A map of environment variable names to the FQDNs of your cluster UIs.
- `clustersConfig`: The raw YAML content defining your clusters, just like the `clusters.yaml` file.

#### Installation
1.  **Navigate to the Helm directory:**
    ```bash
    cd helm
    ```
2.  **Install the chart:**
    ```bash
    helm install <release-name> . --namespace <your-namespace> --create-namespace -f values.yaml
    ```
    Replace `<release-name>` and `<your-namespace>` with your desired values.

## API Endpoints

For detailed information on all available API endpoints, you can access the interactive Swagger UI at `/docs` on your deployed instance.

- `GET /api/resources`: List and search for resources.
- `GET /api/resources/{resource_id}`: Inspect a single resource by its ID.
- `GET /filters/*`: Get unique values for filters like cluster names, namespaces, and resource types.
- `GET /api/related-namespaces`: Find all namespaces (and their corresponding clusters) where a resource with a specific name and type exists.