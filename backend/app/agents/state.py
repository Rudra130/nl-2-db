"""Agent Workflow State Schema."""
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict):
    # Input
    user_prompt: str
    database_type: str
    connector_id: str

    # Intent Classification
    intent: Optional[str]
    intent_reasoning: Optional[str]
    is_safe: bool

    # Schema Context
    schema_summary: Optional[str]
    selected_tables: List[str]

    # Query Generation
    generated_query: Optional[str]
    query_explanation: Optional[str]

    # Validation
    is_valid: bool
    validation_error: Optional[str]
    retry_count: int

    # Execution
    execution_result: Optional[Dict[str, Any]]
    execution_error: Optional[str]

    # Result Interpretation & Summary
    summary: Optional[str]
    insights: List[str]

    # Final Lifecycle Status
    status: str  # "success" | "rejected" | "error"
    error_message: Optional[str]
