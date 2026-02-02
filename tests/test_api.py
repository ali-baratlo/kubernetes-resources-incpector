import pytest
import json
from fastapi.testclient import TestClient
from mongomock import MongoClient
from bson import ObjectId
from main import app
from utils.db import get_resource_collection

# Create a mock MongoDB client
mock_client = MongoClient()
db = mock_client.odin

# Sample data for testing
resources_to_insert = [
    {
        "_id": ObjectId("60d5f3f7e4b0c8b4b8b4b8b1"),
        "cluster_name": "test-cluster-1",
        "namespace": "default",
        "resource_type": "ConfigMap",
        "resource_name": "my-configmap",
        "resource_version": "1",
        "data": {"key": "value"},
    },
    {
        "_id": ObjectId("60d5f3f7e4b0c8b4b8b4b8b2"),
        "cluster_name": "test-cluster-1",
        "namespace": "kube-system",
        "resource_type": "Secret",
        "resource_name": "my-secret",
        "resource_version": "2",
        "data": {"user": "YWRtaW4="},
    },
    {
        "_id": ObjectId("60d5f3f7e4b0c8b4b8b4b8b3"),
        "cluster_name": "test-cluster-2",
        "namespace": "default",
        "resource_type": "Deployment",
        "resource_name": "my-deployment",
        "resource_version": "3",
        "data": {"replicas": 3},
    },
]

# Add the full_resource_string to each document before insertion
for r in resources_to_insert:
    # Create a copy for stringifying that doesn't have the ObjectId
    r_copy = {k: v for k, v in r.items() if k != "_id"}
    r["full_resource_string"] = json.dumps(r_copy)

db.resources.insert_many(resources_to_insert)

def override_get_resource_collection():
    """Override for dependency injection to use the mock database."""
    return db.resources

# Apply the dependency override
app.dependency_overrides[get_resource_collection] = override_get_resource_collection

@pytest.fixture(scope="module")
def client():
    """
    Test client fixture for making requests to the FastAPI app.
    """
    with TestClient(app) as c:
        yield c

def test_list_resources(client):
    response = client.get("/api/resources")
    assert response.status_code == 200
    assert len(response.json()) == 3

def test_list_resources_with_filter(client):
    response = client.get("/api/resources?cluster_name=test-cluster-1")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/api/resources?namespace=default")
    assert response.status_code == 200
    assert len(response.json()) == 2

    response = client.get("/api/resources?resource_type=Secret")
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_resource(client):
    # Use a known ID from the sample data
    resource_id = "60d5f3f7e4b0c8b4b8b4b8b1"
    response = client.get(f"/api/resources/{resource_id}")
    assert response.status_code == 200
    assert response.json()["resource_name"] == "my-configmap"

def test_get_resource_not_found(client):
    response = client.get("/api/resources/60d5f3f7e4b0c8b4b8b4b8b4") # A non-existent ID
    assert response.status_code == 404

def test_search_resources(client):
    # Search by resource name
    response = client.get("/api/resources?keyword=my-configmap")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["resource_name"] == "my-configmap"

    # Search by a value in the data field
    response = client.get("/api/resources?keyword=replicas")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["resource_name"] == "my-deployment"

def test_get_filters(client):
    response = client.get("/filters/cluster_names")
    assert response.status_code == 200
    assert "test-cluster-1" in response.json()
    assert "test-cluster-2" in response.json()

    response = client.get("/filters/namespaces")
    assert response.status_code == 200
    assert "default" in response.json()
    assert "kube-system" in response.json()

    response = client.get("/filters/resource_types")
    assert response.status_code == 200
    assert "ConfigMap" in response.json()
    assert "Secret" in response.json()
    assert "Deployment" in response.json()