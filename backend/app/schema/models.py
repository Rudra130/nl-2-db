"""Schema metadata data structures and helper utilities."""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from backend.app.connectors.base import (
    ColumnMetadata,
    TableMetadata,
    RelationshipMetadata,
    SchemaMetadata,
)


class SchemaPruningRequest(BaseModel):
    query_text: str
    all_tables: List[str]


class SchemaPruningResponse(BaseModel):
    selected_tables: List[str]
    reasoning: str = ""
