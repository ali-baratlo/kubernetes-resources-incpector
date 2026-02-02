from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class Resource(BaseModel):
    cluster_name: str = Field(..., description="The name of the Kubernetes/OKD cluster.")
    namespace: str = Field(..., description="The namespace of the resource.")
    environment: str = Field(..., description="The environment of the resource (e.g., production, non-production).")
    resource_type: str = Field(..., description="The type of the resource (e.g., Deployment, Pod).")
    resource_name: str = Field(..., description="The name of the resource.")
    resource_version: str = Field(..., description="The resource version from Kubernetes metadata.")
    data: Dict[str, Any] = Field(..., description="The full JSON representation of the resource.")
    full_resource_string: str = Field(description="The stringified full resource for searching.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the resource was stored.")

    class Config:
        collection_name = "resources"

class AuditLog(BaseModel):
    resource_id: str = Field(..., description="The ID of the resource that was changed.")
    old_version: Optional[str] = Field(None, description="The previous resource version.")
    new_version: str = Field(..., description="The new resource version.")
    diff: Dict[str, Any] = Field(..., description="The diff between the old and new resource data.")
    changed_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp of the change.")

    class Config:
        collection_name = "audit_logs"