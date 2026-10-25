"""PostgreSQL Database Connector."""
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


class PostgreSQLConnector(BaseConnector):
    """Connector for PostgreSQL databases using asyncpg."""

    def __init__(
        self,
        name: str,
        host: str = "localhost",
        port: int = 5432,
        user: str = "postgres",
        password: str = "postgres",
        database: str = "nl2db_test",
        schema_name: str = "public",
    ):
        super().__init__(name=name, database_type="postgres")
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.schema_name = schema_name
        pwd = f":{password}" if password else ""
        self.url = f"postgresql+asyncpg://{user}{pwd}@{host}:{port}/{database}"
        self.engine: Optional[AsyncEngine] = None

    async def connect(self) -> None:
        if not self.engine:
            self.engine = create_async_engine(
                self.url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=False,
            )

    async def test_connection(self) -> bool:
        await self.connect()
        assert self.engine is not None
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1;"))
            return True
        except Exception:
            return False

    async def get_tables(self) -> List[str]:
        await self.connect()
        assert self.engine is not None
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = :schema AND table_type = 'BASE TABLE';
        """
        async with self.engine.connect() as conn:
            res = await conn.execute(text(query), {"schema": self.schema_name})
            return [row[0] for row in res.fetchall()]

    async def get_schema(self, force_refresh: bool = False) -> SchemaMetadata:
        if self._schema_cache and not force_refresh:
            return self._schema_cache

        await self.connect()
        assert self.engine is not None

        tables_meta: List[TableMetadata] = []
        relationships: List[RelationshipMetadata] = []

        table_names = await self.get_tables()

        async with self.engine.connect() as conn:
            # Query columns
            col_query = """
                SELECT 
                    table_name, column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_schema = :schema
                ORDER BY table_name, ordinal_position;
            """
            col_res = await conn.execute(text(col_query), {"schema": self.schema_name})
            col_rows = col_res.mappings().fetchall()

            # Query primary keys
            pk_query = """
                SELECT
                    tc.table_name, ccu.column_name
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.constraint_column_usage AS ccu
                  ON tc.constraint_name = ccu.constraint_name
                  AND tc.table_schema = ccu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema = :schema;
            """
            pk_res = await conn.execute(text(pk_query), {"schema": self.schema_name})
            pk_rows = pk_res.mappings().fetchall()

            pks_by_table: Dict[str, List[str]] = {}
            for pk in pk_rows:
                pks_by_table.setdefault(pk["table_name"], []).append(pk["column_name"])

            # Query foreign keys
            fk_query = """
                SELECT
                    kcu.table_name AS from_table,
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM information_schema.table_constraints AS tc
                JOIN information_schema.key_column_usage AS kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage AS ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = :schema;
            """
            fk_res = await conn.execute(text(fk_query), {"schema": self.schema_name})
            fk_rows = fk_res.mappings().fetchall()

            fk_by_table: Dict[str, List[Dict[str, str]]] = {}
            for fk in fk_rows:
                from_t = fk["from_table"]
                fk_by_table.setdefault(from_t, []).append({
                    "from": fk["from_column"],
                    "to_table": fk["to_table"],
                    "to_col": fk["to_column"],
                })
                relationships.append(
                    RelationshipMetadata(
                        from_table=from_t,
                        from_column=fk["from_column"],
                        to_table=fk["to_table"],
                        to_column=fk["to_column"],
                    )
                )

            # Map columns
            cols_by_table: Dict[str, List[ColumnMetadata]] = {}
            for cr in col_rows:
                t = cr["table_name"]
                c_name = cr["column_name"]
                is_pk = c_name in pks_by_table.get(t, [])

                fk_ref = None
                for fk in fk_by_table.get(t, []):
                    if fk["from"] == c_name:
                        fk_ref = f"{fk['to_table']}.{fk['to_col']}"
                        break

                cols_by_table.setdefault(t, []).append(
                    ColumnMetadata(
                        name=c_name,
                        data_type=cr["data_type"],
                        nullable=cr["is_nullable"] == "YES",
                        is_primary_key=is_pk,
                        foreign_key=fk_ref,
                    )
                )

            for t_name in table_names:
                tables_meta.append(
                    TableMetadata(
                        name=t_name,
                        columns=cols_by_table.get(t_name, []),
                        primary_keys=pks_by_table.get(t_name, []),
                        foreign_keys=fk_by_table.get(t_name, []),
                    )
                )

        schema = SchemaMetadata(
            database_type="postgres",
            database_name=self.database,
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
            # Enforce read only transaction on connection level
            async with self.engine.connect() as conn:
                await conn.execute(text("SET TRANSACTION READ ONLY;"))
                stmt = text(query)
                res = await conn.execute(stmt, params or {})
                cols = list(res.keys())
                fetched = [dict(row) for row in res.mappings().fetchall()]
                return cols, fetched

        try:
            cols, rows = await run_with_timeout(_exec(), timeout_seconds=timeout_seconds, operation_name="PostgreSQL Query")
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
