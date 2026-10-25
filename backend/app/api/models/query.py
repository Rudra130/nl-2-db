"""Query API Request and Response Schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    prompt: str = Field(..., description="User natural language question", min_length=1)
    connector_id: str = Field(default="sqlite", description="Target database identifier (e.g., sqlite, mongodb, mysql, postgres)")


class QueryResponse(BaseModel):
    query_id: str
    status: str  # "success" | "rejected" | "error"
    database_type: str
    connector_id: str
    user_prompt: str
    generated_query: Optional[str] = None
    query_explanation: Optional[str] = None
    is_valid: bool = False
    retry_count: int = 0
    columns: List[str] = Field(default_factory=list)
    rows: List[Dict[str, Any]] = Field(default_factory=list)
    row_count: int = 0
    execution_time_ms: float = 0.0
    summary: Optional[str] = None
    insights: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
