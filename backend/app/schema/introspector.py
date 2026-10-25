"""Schema Introspector with in-memory TTL caching."""
import time
from typing import Dict, List, Optional, Tuple
from backend.app.connectors.base import BaseConnector, SchemaMetadata, TableMetadata


class SchemaIntrospector:
    """Introspects and caches database schemas with a configurable TTL."""

    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[float, SchemaMetadata]] = {}

    async def get_schema(
        self, connector: BaseConnector, force_refresh: bool = False
    ) -> SchemaMetadata:
        key = f"{connector.database_type}:{connector.name}"
        now = time.time()

        if not force_refresh and key in self._cache:
            cached_time, schema = self._cache[key]
            if now - cached_time < self.ttl_seconds:
                return schema

        schema = await connector.get_schema(force_refresh=True)
        self._cache[key] = (now, schema)
        return schema

    def prune_schema(
        self, schema: SchemaMetadata, relevant_table_names: List[str]
    ) -> SchemaMetadata:
        """Return a copy of the schema containing only the specified tables and their relationships."""
        if not relevant_table_names:
            return schema

        lookup = {name.lower() for name in relevant_table_names}
        pruned_tables = [t for t in schema.tables if t.name.lower() in lookup]
        pruned_rel = [
            r
            for r in schema.relationships
            if r.from_table.lower() in lookup and r.to_table.lower() in lookup
        ]

        return SchemaMetadata(
            database_type=schema.database_type,
            database_name=schema.database_name,
            tables=pruned_tables,
            relationships=pruned_rel,
        )

    def format_for_prompt(
        self, schema: SchemaMetadata, relevant_tables: Optional[List[str]] = None
    ) -> str:
        """Format the schema metadata into a clean, concise prompt representation."""
        target_schema = self.prune_schema(schema, relevant_tables) if relevant_tables else schema
        return target_schema.to_compact_summary()

    def invalidate(self, connector: Optional[BaseConnector] = None) -> None:
        if connector:
            key = f"{connector.database_type}:{connector.name}"
            self._cache.pop(key, None)
        else:
            self._cache.clear()


_global_introspector: Optional[SchemaIntrospector] = None


def get_schema_introspector() -> SchemaIntrospector:
    global _global_introspector
    if _global_introspector is None:
        _global_introspector = SchemaIntrospector()
    return _global_introspector
