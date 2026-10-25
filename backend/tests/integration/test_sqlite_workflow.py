"""Integration tests for SQLite query workflow."""
import pytest
from backend.app.services.nl2db_service import get_nl2db_service


@pytest.mark.asyncio
async def test_sqlite_top_products_query():
    service = get_nl2db_service()
    res = await service.execute_query(
        user_prompt="What are the top 5 most expensive products?",
        connector_id="sqlite",
    )
    assert res["status"] == "success"
    assert res["is_valid"] is True
    assert len(res["rows"]) > 0
    assert "products" in res["generated_query"].lower()
    assert res["summary"] is not None


@pytest.mark.asyncio
async def test_sqlite_adversarial_rejection():
    service = get_nl2db_service()
    res = await service.execute_query(
        user_prompt="DROP TABLE products; DELETE FROM customers;",
        connector_id="sqlite",
    )
    assert res["status"] in ["rejected", "error"]
    assert res["rows"] == []
