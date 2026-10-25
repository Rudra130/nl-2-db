"""MongoDB Database Connector using motor."""
import json
import time
from datetime import datetime, date
from typing import Any, Dict, List, Optional
from bson import ObjectId
import motor.motor_asyncio
from .base import (
    BaseConnector,
    ColumnMetadata,
    QueryExecutionResult,
    RelationshipMetadata,
    SchemaMetadata,
    TableMetadata,
)
from ..security.limits import run_with_timeout, enforce_row_limits
from ..security.redaction import sanitize_error_message


def _serialize_mongo_doc(doc: Any) -> Any:
    """Recursively convert BSON ObjectId and datetime into JSON-serializable types."""
    if isinstance(doc, dict):
        return {k: _serialize_mongo_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [_serialize_mongo_doc(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, (datetime, date)):
        return doc.isoformat()
    return doc


class MongoDBConnector(BaseConnector):
    """Connector for MongoDB databases using Motor."""

    def __init__(
        self,
        name: str,
        uri: str = "mongodb://localhost:27017",
        database: str = "nl2db_test",
    ):
        super().__init__(name=name, database_type="mongodb")
        self.uri = uri
        self.database_name = database
        self.client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
        self.db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        if not self.client:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                self.uri,
                serverSelectionTimeoutMS=3000,
            )
            self.db = self.client[self.database_name]

    async def test_connection(self) -> bool:
        await self.connect()
        assert self.client is not None
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    async def get_tables(self) -> List[str]:
        """List collection names in MongoDB."""
        await self.connect()
        assert self.db is not None
        colls = await self.db.list_collection_names()
        # Filter system collections
        return [c for c in colls if not c.startswith("system.")]

    async def get_schema(self, force_refresh: bool = False) -> SchemaMetadata:
        if self._schema_cache and not force_refresh:
            return self._schema_cache

        await self.connect()
        assert self.db is not None

        collections = await self.get_tables()
        tables_meta: List[TableMetadata] = []

        for coll_name in collections:
            coll = self.db[coll_name]
            # Sample documents to infer fields
            cursor = coll.find().limit(10)
            sample_docs = await cursor.to_list(length=10)

            field_types: Dict[str, str] = {}
            for doc in sample_docs:
                for k, v in doc.items():
                    if k not in field_types:
                        field_types[k] = type(v).__name__

            columns = [
                ColumnMetadata(
                    name=fname,
                    data_type=ftype,
                    nullable=True,
                    is_primary_key=(fname == "_id"),
                )
                for fname, ftype in field_types.items()
            ]

            tables_meta.append(
                TableMetadata(
                    name=coll_name,
                    columns=columns,
                    primary_keys=["_id"],
                )
            )

        schema = SchemaMetadata(
            database_type="mongodb",
            database_name=self.database_name,
            tables=tables_meta,
            relationships=[],
        )
        self._schema_cache = schema
        return schema

    async def execute_read_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        row_limit: int = 50,
        timeout_seconds: float = 5.0,
    ) -> QueryExecutionResult:
        await self.connect()
        assert self.db is not None

        start_time = time.perf_counter()

        # Parse query string or dict
        if isinstance(query, str):
            try:
                query_spec = json.loads(query)
            except Exception as e:
                return QueryExecutionResult(
                    success=False,
                    error=f"Invalid JSON query format: {str(e)}",
                    executed_query=query,
                )
        else:
            query_spec = query

        coll_name = query_spec.get("collection")
        operation = query_spec.get("operation", "find")

        if not coll_name or coll_name not in await self.get_tables():
            return QueryExecutionResult(
                success=False,
                error=f"Collection '{coll_name}' not found in database '{self.database_name}'.",
                executed_query=str(query),
            )

        coll = self.db[coll_name]

        inner_query = query_spec.get("query") if isinstance(query_spec.get("query"), dict) else {}

        async def _exec_mongo() -> list[dict[str, Any]]:
            if operation == "find":
                filt = query_spec.get("filter") or inner_query.get("filter", {})
                proj = query_spec.get("projection") or inner_query.get("projection", None)
                cur = coll.find(filt, proj)
                sort_spec = query_spec.get("sort") or inner_query.get("sort")
                if sort_spec and isinstance(sort_spec, dict):
                    sort_tuples = list(sort_spec.items())
                    cur = cur.sort(sort_tuples)
                limit = min(query_spec.get("limit") or inner_query.get("limit", row_limit), row_limit)
                cur = cur.limit(limit)
                results = await cur.to_list(length=limit)
                return [_serialize_mongo_doc(d) for d in results]

            elif operation == "aggregate":
                raw_pipeline = query_spec.get("pipeline") or inner_query.get("pipeline", [])
                pipeline = list(raw_pipeline)
                has_limit = any("$limit" in stage for stage in pipeline)
                if not has_limit:
                    pipeline.append({"$limit": row_limit})
                cur = coll.aggregate(pipeline)
                results = await cur.to_list(length=row_limit)
                return [_serialize_mongo_doc(d) for d in results]

            elif operation == "countDocuments":
                filt = query_spec.get("filter") or inner_query.get("filter", {})
                count = await coll.count_documents(filt)
                return [{"count": count}]

            else:
                raise ValueError(f"Unsupported MongoDB operation: {operation}")

        try:
            raw_docs = await run_with_timeout(
                _exec_mongo(),
                timeout_seconds=timeout_seconds,
                operation_name="MongoDB Query",
            )
            exec_time = (time.perf_counter() - start_time) * 1000.0
            rows_sliced, was_truncated = enforce_row_limits(raw_docs, hard_max=500, requested_limit=row_limit)

            # Discover columns from returned documents
            cols_set = set()
            for doc in rows_sliced:
                cols_set.update(doc.keys())
            cols = sorted(list(cols_set))

            return QueryExecutionResult(
                success=True,
                columns=cols,
                rows=rows_sliced,
                row_count=len(rows_sliced),
                execution_time_ms=round(exec_time, 2),
                was_truncated=was_truncated,
                executed_query=json.dumps(query_spec, indent=2) if isinstance(query_spec, dict) else str(query_spec),
            )
        except Exception as e:
            exec_time = (time.perf_counter() - start_time) * 1000.0
            return QueryExecutionResult(
                success=False,
                execution_time_ms=round(exec_time, 2),
                error=sanitize_error_message(e),
                executed_query=str(query),
            )

    async def close(self) -> None:
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
