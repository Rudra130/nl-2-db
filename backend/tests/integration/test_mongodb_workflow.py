"""Integration tests for MongoDB workflow."""
import pytest
from backend.app.services.nl2db_service import get_nl2db_service
from backend.app.connectors.registry import get_connector_registry


@pytest.mark.asyncio
async def test_mongodb_connection_and_query():
    registry = get_connector_registry()
    mongo_conn = registry.get_connector("mongodb")
    connected = await mongo_conn.test_connection()
    if not connected:
        pytest.skip("Local MongoDB is not running, skipping live Mongo test.")

    service = get_nl2db_service()
    res = await service.execute_query(
        user_prompt="Show top 5 expensive products",
        connector_id="mongodb",
    )
    assert res["status"] == "success"
    assert res["is_valid"] is True
    assert len(res["rows"]) > 0
    assert res["summary"] is not None
