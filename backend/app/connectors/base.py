"""Base Database Connector Interface and Metadata Models."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ColumnMetadata(BaseModel):
    name: str
    data_type: str
    nullable: bool = True
    is_primary_key: bool = False
    foreign_key: Optional[str] = None
    description: Optional[str] = None


class TableMetadata(BaseModel):
    name: str
    columns: List[ColumnMetadata] = Field(default_factory=list)
    primary_keys: List[str] = Field(default_factory=list)
    foreign_keys: List[Dict[str, str]] = Field(default_factory=list)
    row_count_estimate: Optional[int] = None
    description: Optional[str] = None


class RelationshipMetadata(BaseModel):
    from_table: str
    from_column: str
    to_table: str
    to_column: str


class SchemaMetadata(BaseModel):
    database_type: str
    database_name: str
    tables: List[TableMetadata] = Field(default_factory=list)
    relationships: List[RelationshipMetadata] = Field(default_factory=list)

    def get_table_names(self) -> List[str]:
        return [t.name for t in self.tables]

    def to_compact_summary(self) -> str:
        """Compact text format for injecting into LLM context."""
        lines = [f"Database: {self.database_name} ({self.database_type.upper()})"]
        for t in self.tables:
            col_strs = []
            for c in t.columns:
                pk_flag = " [PK]" if c.is_primary_key else ""
                fk_flag = f" [FK -> {c.foreign_key}]" if c.foreign_key else ""
                col_strs.append(f"{c.name} ({c.data_type}{pk_flag}{fk_flag})")
            lines.append(f"- Table `{t.name}`: {', '.join(col_strs)}")

        if self.relationships:
            lines.append("\nRelationships:")
            for r in self.relationships:
                lines.append(f"- `{r.from_table}`.{r.from_column} -> `{r.to_table}`.{r.to_column}")

        return "\n".join(lines)


class QueryExecutionResult(BaseModel):
    success: bool
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    was_truncated: bool = False
    error: Optional[str] = None
    executed_query: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)


class BaseConnector(ABC):
    """Abstract Base Class for all Database Connectors."""

    def __init__(self, name: str, database_type: str):
        self.name = name
        self.database_type = database_type
        self._schema_cache: Optional[SchemaMetadata] = None

    @abstractmethod
    async def connect(self) -> None:
        """Establish database connection or pool."""
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """Verify database connectivity."""
        pass

    @abstractmethod
    async def get_schema(self, force_refresh: bool = False) -> SchemaMetadata:
        """Inspect and return schema metadata."""
        pass

    @abstractmethod
    async def get_tables(self) -> List[str]:
        """List accessible tables or collections."""
        pass

    @abstractmethod
    async def execute_read_query(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        row_limit: int = 50,
        timeout_seconds: float = 5.0,
    ) -> QueryExecutionResult:
        """Execute validated read-only query."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Gracefully release connections."""
        pass
