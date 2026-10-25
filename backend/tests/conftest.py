"""Pytest fixtures and configuration."""
import os
import sys
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.config import Settings
from backend.app.main import app


@pytest.fixture(scope="session")
def test_settings():
    return Settings(
        USE_MOCK_LLM=True,
        SQLITE_DB_PATH="./data/nl2db_sample.db",
        MONGODB_URI="mongodb://localhost:27017",
        MONGODB_DATABASE="nl2db_test",
    )


@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
