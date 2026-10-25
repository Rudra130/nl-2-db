"""MySQL Database Connector."""
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


class MySQLConnector(BaseConnector):
    """Connector for MySQL databases using aiomysql."""

    def __init__(
        self,
        name: str,
        host: str = "localhost",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "nl2db_test",
    ):
        super().__init__(name=name, database_type="mysql")
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        pwd = f":{password}" if password else ""
        self.url = f"mysql+aiomysql://{user}{pwd}@{host}:{port}/{database}"
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
            WHERE table_schema = :db AND table_type = 'BASE TABLE';
        """
        async with self.engine.connect() as conn:
            res = await conn.execute(text(query), {"db": self.database})
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
            # Query all columns for this schema
            col_query = """
                SELECT 
                    table_name, column_name, data_type, is_nullable, column_key, column_comment
                FROM information_schema.columns 
                WHERE table_schema = :db
                ORDER BY table_name, ordinal_position;
            """
            col_res = await conn.execute(text(col_query), {"db": self.database})
            col_rows = col_res.mappings().fetchall()

            # Query all foreign keys
            fk_query = """
                SELECT 
                    table_name, column_name, referenced_table_name, referenced_column_name
                FROM information_schema.key_column_usage
                WHERE table_schema = :db 
                  AND referenced_table_name IS NOT NULL;
            """
            fk_res = await conn.execute(text(fk_query), {"db": self.database})
            fk_rows = fk_res.mappings().fetchall()

            # Group foreign keys
            fk_by_table: Dict[str, List[Dict[str, str]]] = {}
            for fk in fk_rows:
                fk_d = {str(k).lower(): v for k, v in fk.items()}
                t = fk_d.get("table_name", "")
                c_name = fk_d.get("column_name", "")
                to_tbl = fk_d.get("referenced_table_name", "")
                to_col = fk_d.get("referenced_column_name", "")
                fk_by_table.setdefault(t, []).append({
                    "from": c_name,
                    "to_table": to_tbl,
                    "to_col": to_col,
                })
                relationships.append(
                    RelationshipMetadata(
                        from_table=t,
                        from_column=c_name,
                        to_table=to_tbl,
                        to_column=to_col,
                    )
                )

            # Group columns by table
            cols_by_table: Dict[str, List[ColumnMetadata]] = {}
            pks_by_table: Dict[str, List[str]] = {}

            for cr in col_rows:
                cr_d = {str(k).lower(): v for k, v in cr.items()}
                t = cr_d.get("table_name", "")
                c_name = cr_d.get("column_name", "")
                is_pk = cr_d.get("column_key") == "PRI"
                if is_pk:
                    pks_by_table.setdefault(t, []).append(c_name)

                # Check foreign key
                fk_ref = None
                for fk in fk_by_table.get(t, []):
                    if fk["from"] == c_name:
                        fk_ref = f"{fk['to_table']}.{fk['to_col']}"
                        break

                cols_by_table.setdefault(t, []).append(
                    ColumnMetadata(
                        name=c_name,
                        data_type=cr_d.get("data_type", "varchar"),
                        nullable=cr_d.get("is_nullable", "YES").upper() == "YES",
                        is_primary_key=is_pk,
                        foreign_key=fk_ref,
                        description=cr_d.get("column_comment") or None,
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
            database_type="mysql",
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
            async with self.engine.connect() as conn:
                # Set transaction read only for defense in depth
                try:
                    await conn.execute(text("SET TRANSACTION READ ONLY;"))
                except Exception:
                    pass
                stmt = text(query)
                res = await conn.execute(stmt, params or {})
                cols = list(res.keys())
                fetched = [dict(row) for row in res.mappings().fetchall()]
                return cols, fetched

        try:
            cols, rows = await run_with_timeout(_exec(), timeout_seconds=timeout_seconds, operation_name="MySQL Query")
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
