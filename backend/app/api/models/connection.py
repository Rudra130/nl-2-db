"""Database Connection API Schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.connectors.base import SchemaMetadata


class ConnectionInfo(BaseModel):
    id: str
    name: str
    database_type: str
    is_sql: bool
    description: str
    is_connected: Optional[bool] = None


class ConnectionTestRequest(BaseModel):
    connector_id: str


class ConnectionTestResponse(BaseModel):
    connector_id: str
    database_type: str
    success: bool
    message: str
