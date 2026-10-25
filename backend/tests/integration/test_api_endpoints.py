"""Integration tests for FastAPI REST API endpoints."""
import pytest


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data


@pytest.mark.asyncio
async def test_connections_list(async_client):
    response = await async_client.get("/api/v1/connections")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    ids = [c["id"] for c in data]
    assert "sqlite" in ids
    assert "mongodb" in ids


@pytest.mark.asyncio
async def test_sqlite_schema_endpoint(async_client):
    response = await async_client.get("/api/v1/connections/sqlite/schema")
    assert response.status_code == 200
    data = response.json()
    assert data["database_type"] == "sqlite"
    table_names = [t["name"] for t in data["tables"]]
    assert "products" in table_names
    assert "customers" in table_names


@pytest.mark.asyncio
async def test_query_endpoint(async_client):
    response = await async_client.post(
        "/api/v1/query",
        json={"prompt": "Show top 5 expensive products", "connector_id": "sqlite"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["row_count"] > 0
    assert len(data["columns"]) > 0
    assert data["summary"] is not None
