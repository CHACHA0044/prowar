"""
Health check and system status schemas.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    status: str = Field(..., description="'healthy' or 'unhealthy'")
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class SystemHealthResponse(BaseModel):
    status: str = Field(..., description="Overall system health status")
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "0.1.0"
    components: Dict[str, ComponentHealth]


class DatabaseHealthResponse(BaseModel):
    status: str
    connected: bool
    dialect: str
    url_type: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

