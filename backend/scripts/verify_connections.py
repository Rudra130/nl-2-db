"""Verify connectivity to all configured database instances."""
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.app.config import get_settings
from backend.app.connectors.registry import get_connector_registry


async def main() -> None:
    settings = get_settings()
    print("=" * 60)
    print("NL2DB Database Connectivity Verification")
    print("=" * 60)
    print(f"Target MySQL:      {settings.MYSQL_HOST}:{settings.MYSQL_PORT} / {settings.MYSQL_DATABASE} (user: {settings.MYSQL_USER})")
    print(f"Target PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT} / {settings.POSTGRES_DATABASE} (user: {settings.POSTGRES_USER})")
    print(f"Target MongoDB:    {settings.MONGODB_URI} / {settings.MONGODB_DATABASE}")
    print(f"Target SQLite:     {settings.SQLITE_DB_PATH}")
    print("-" * 60)

    registry = get_connector_registry()
    connectors = registry.list_connectors()

    for item in connectors:
        cid = item["id"]
        conn = registry.get_connector(cid)
        print(f"Testing [{cid.upper()}] ... ", end="", flush=True)
        try:
            ok = await conn.test_connection()
            if ok:
                print("SUCCESS (Connected)")
            else:
                print("FAILED (Check credentials or service status)")
        except Exception as e:
            print(f"ERROR: {str(e)}")

    await registry.close_all()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
