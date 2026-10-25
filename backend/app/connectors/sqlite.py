"""SQLite Database Connector."""
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy import text
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


class SQLiteConnector(BaseConnector):
    """Connector for SQLite databases."""

    def __init__(self, name: str, db_path: str):
        super().__init__(name=name, database_type="sqlite")
        self.db_path = db_path
        self.url = f"sqlite+aiosqlite:///{db_path}"
        self.engine: Optional[AsyncEngine] = None

    async def connect(self) -> None:
        if not self.engine:
            self.engine = create_async_engine(self.url, echo=False)

    async def test_connection(self) -> bool:
        await self.connect()
        assert self.engine is not None
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False

    async def get_tables(self) -> List[str]:
        await self.connect()
        assert self.engine is not None
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        async with self.engine.connect() as conn:
            result = await conn.execute(text(query))
            return [row[0] for row in result.fetchall()]

    async def get_schema(self, force_refresh: bool = False) -> SchemaMetadata:
        if self._schema_cache and not force_refresh:
            return self._schema_cache

        await self.connect()
        assert self.engine is not None

        tables_meta: List[TableMetadata] = []
        relationships: List[RelationshipMetadata] = []

        table_names = await self.get_tables()

        async with self.engine.connect() as conn:
            for t_name in table_names:
                # 1. Columns via PRAGMA table_info
                col_res = await conn.execute(text(f"PRAGMA table_info(`{t_name}`);"))
                columns: List[ColumnMetadata] = []
                pks: List[str] = []

                for row in col_res.mappings():
                    # cid, name, type, notnull, dflt_value, pk
                    is_pk = bool(row["pk"])
                    c_name = row["name"]
                    if is_pk:
                        pks.append(c_name)

                    columns.append(
                        ColumnMetadata(
                            name=c_name,
                            data_type=row["type"] or "TEXT",
                            nullable=not bool(row["notnull"]),
                            is_primary_key=is_pk,
                        )
                    )

                # 2. Foreign keys via PRAGMA foreign_key_list
                fk_res = await conn.execute(text(f"PRAGMA foreign_key_list(`{t_name}`);"))
                fks_list = []
                for fk_row in fk_res.mappings():
                    # id, seq, table, from, to, on_update, on_delete, match
                    to_tbl = fk_row["table"]
                    from_col = fk_row["from"]
                    to_col = fk_row["to"]
                    fks_list.append({"from": from_col, "to_table": to_tbl, "to_col": to_col})

                    relationships.append(
                        RelationshipMetadata(
                            from_table=t_name,
                            from_column=from_col,
                            to_table=to_tbl,
                            to_column=to_col,
                        )
                    )

                    # Mark column foreign_key
                    for col in columns:
                        if col.name == from_col:
                            col.foreign_key = f"{to_tbl}.{to_col}"

                tables_meta.append(
                    TableMetadata(
                        name=t_name,
                        columns=columns,
                        primary_keys=pks,
                        foreign_keys=fks_list,
                    )
                )

        schema = SchemaMetadata(
            database_type="sqlite",
            database_name=self.name,
            tables=tables_meta,
            relationships=relationships,
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
        assert self.engine is not None

        start_time = time.perf_counter()

        async def _exec() -> tuple[list[str], list[dict[str, Any]]]:
            assert self.engine is not None
            async with self.engine.connect() as conn:
                stmt = text(query)
                res = await conn.execute(stmt, params or {})
                cols = list(res.keys())
                fetched = [dict(row) for row in res.mappings().fetchall()]
                return cols, fetched

        try:
            cols, rows = await run_with_timeout(_exec(), timeout_seconds=timeout_seconds, operation_name="SQLite Query")
            exec_time = (time.perf_counter() - start_time) * 1000.0

            rows_sliced, was_truncated = enforce_row_limits(rows, hard_max=500, requested_limit=row_limit)

            return QueryExecutionResult(
                success=True,
                columns=cols,
                rows=rows_sliced,
                row_count=len(rows_sliced),
                execution_time_ms=round(exec_time, 2),
                was_truncated=was_truncated,
                executed_query=query,
                parameters=params or {},
            )
        except Exception as e:
            exec_time = (time.perf_counter() - start_time) * 1000.0
            return QueryExecutionResult(
                success=False,
                execution_time_ms=round(exec_time, 2),
                error=sanitize_error_message(e),
                executed_query=query,
                parameters=params or {},
            )

    async def close(self) -> None:
        if self.engine:
            await self.engine.dispose()
            self.engine = None
