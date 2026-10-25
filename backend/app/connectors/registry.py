"""Connector Registry and Capability Management."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from .base import BaseConnector
from .mysql import MySQLConnector
from .postgres import PostgreSQLConnector
from .sqlite import SQLiteConnector
from .mongodb import MongoDBConnector
from ..config import Settings, get_settings


class DatabaseCapability(BaseModel):
    database_type: str
    is_sql: bool
    dialect: str
    supports_joins: bool
    supports_transactions: bool
    description: str


CAPABILITY_REGISTRY: Dict[str, DatabaseCapability] = {
    "mysql": DatabaseCapability(
        database_type="mysql",
        is_sql=True,
        dialect="mysql",
        supports_joins=True,
        supports_transactions=True,
        description="MySQL Relational Database",
    ),
    "postgres": DatabaseCapability(
        database_type="postgres",
        is_sql=True,
        dialect="postgres",
        supports_joins=True,
        supports_transactions=True,
        description="PostgreSQL Relational Database",
    ),
    "sqlite": DatabaseCapability(
        database_type="sqlite",
        is_sql=True,
        dialect="sqlite",
        supports_joins=True,
        supports_transactions=True,
        description="SQLite File-based Database",
    ),
    "mongodb": DatabaseCapability(
        database_type="mongodb",
        is_sql=False,
        dialect="mongodb",
        supports_joins=False,
        supports_transactions=False,
        description="MongoDB Document Database",
    ),
}


class ConnectorRegistry:
    """Registry managing active connector instances."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._connectors: Dict[str, BaseConnector] = {}
        self._initialize_default_connectors()

    def _initialize_default_connectors(self) -> None:
        # 1. MySQL
        self._connectors["mysql"] = MySQLConnector(
            name="mysql_local",
            host=self.settings.MYSQL_HOST,
            port=self.settings.MYSQL_PORT,
            user=self.settings.MYSQL_USER,
            password=self.settings.MYSQL_PASSWORD,
            database=self.settings.MYSQL_DATABASE,
        )

        # 2. PostgreSQL
        self._connectors["postgres"] = PostgreSQLConnector(
            name="postgres_local",
            host=self.settings.POSTGRES_HOST,
            port=self.settings.POSTGRES_PORT,
            user=self.settings.POSTGRES_USER,
            password=self.settings.POSTGRES_PASSWORD,
            database=self.settings.POSTGRES_DATABASE,
        )

        # 3. MongoDB
        self._connectors["mongodb"] = MongoDBConnector(
            name="mongodb_local",
            uri=self.settings.MONGODB_URI,
            database=self.settings.MONGODB_DATABASE,
        )

        # 4. SQLite
        self._connectors["sqlite"] = SQLiteConnector(
            name="sqlite_local",
            db_path=self.settings.SQLITE_DB_PATH,
        )

    def get_connector(self, name_or_type: str) -> BaseConnector:
        key = name_or_type.lower()
        if key in self._connectors:
            return self._connectors[key]
        # Match by database_type
        for conn in self._connectors.values():
            if conn.database_type.lower() == key:
                return conn
        raise ValueError(f"No connector registered for '{name_or_type}'. Available: {list(self._connectors.keys())}")

    def get_capability(self, database_type: str) -> DatabaseCapability:
        db_type = database_type.lower()
        if db_type in CAPABILITY_REGISTRY:
            return CAPABILITY_REGISTRY[db_type]
        raise ValueError(f"Unknown database type '{database_type}'.")

    def list_connectors(self) -> List[Dict[str, Any]]:
        result = []
        for key, conn in self._connectors.items():
            cap = self.get_capability(conn.database_type)
            result.append({
                "id": key,
                "name": conn.name,
                "database_type": conn.database_type,
                "is_sql": cap.is_sql,
                "description": cap.description,
            })
        return result

    async def close_all(self) -> None:
        for conn in self._connectors.values():
            try:
                await conn.close()
            except Exception:
                pass


_registry_instance: Optional[ConnectorRegistry] = None


def get_connector_registry() -> ConnectorRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ConnectorRegistry()
    return _registry_instance
