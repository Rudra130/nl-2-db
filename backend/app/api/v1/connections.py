"""Database Connection and Schema Endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException
from backend.app.connectors.registry import get_connector_registry
from backend.app.schema.introspector import get_schema_introspector
from backend.app.connectors.base import SchemaMetadata
from backend.app.api.models.connection import (
    ConnectionInfo,
    ConnectionTestRequest,
    ConnectionTestResponse,
)

router = APIRouter(prefix="/connections", tags=["Connections"])


@router.get("", response_model=List[ConnectionInfo])
async def list_connections():
    """List all configured database connections with active status."""
    registry = get_connector_registry()
    items = registry.list_connectors()
    result = []

    for item in items:
        conn = registry.get_connector(item["id"])
        try:
            is_connected = await conn.test_connection()
        except Exception:
            is_connected = False

        result.append(
            ConnectionInfo(
                id=item["id"],
                name=item["name"],
                database_type=item["database_type"],
                is_sql=item["is_sql"],
                description=item["description"],
                is_connected=is_connected,
            )
        )
    return result


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(req: ConnectionTestRequest):
    """Test connectivity for a specific connector ID."""
    registry = get_connector_registry()
    try:
        conn = registry.get_connector(req.connector_id)
        ok = await conn.test_connection()
        return ConnectionTestResponse(
            connector_id=req.connector_id,
            database_type=conn.database_type,
            success=ok,
            message="Connection established successfully." if ok else "Connection failed. Check server status or credentials.",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        return ConnectionTestResponse(
            connector_id=req.connector_id,
            database_type="unknown",
            success=False,
            message=f"Connection error: {str(e)}",
        )


@router.get("/{connector_id}/schema", response_model=SchemaMetadata)
async def get_connection_schema(connector_id: str, force_refresh: bool = False):
    """Retrieve database schema metadata for a specified connector."""
    registry = get_connector_registry()
    try:
        conn = registry.get_connector(connector_id)
        introspector = get_schema_introspector()
        schema = await introspector.get_schema(conn, force_refresh=force_refresh)
        return schema
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        from backend.app.security.redaction import sanitize_error_message
        sanitized = sanitize_error_message(str(e))
        raise HTTPException(
            status_code=400,
            detail=f"Could not connect to {connector_id}: {sanitized}. Check host, port, and credentials in your .env file."
        )
