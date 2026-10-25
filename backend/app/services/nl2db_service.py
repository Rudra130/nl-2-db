"""NL2DB High-level Orchestration Service."""
import uuid
from typing import Any, Dict, Optional
from backend.app.connectors.registry import get_connector_registry
from backend.app.agents.graph import nl2db_graph
from backend.app.agents.state import AgentState


class NL2DBService:
    """Service mediating API requests and LangGraph agent workflow execution."""

    def __init__(self):
        self.registry = get_connector_registry()

    async def execute_query(
        self, user_prompt: str, connector_id: str = "sqlite"
    ) -> Dict[str, Any]:
        connector = self.registry.get_connector(connector_id)
        query_id = str(uuid.uuid4())

        initial_state: AgentState = {
            "user_prompt": user_prompt.strip(),
            "database_type": connector.database_type,
            "connector_id": connector_id,
            "intent": None,
            "intent_reasoning": None,
            "is_safe": True,
            "schema_summary": None,
            "selected_tables": [],
            "generated_query": None,
            "query_explanation": None,
            "is_valid": False,
            "validation_error": None,
            "retry_count": 0,
            "execution_result": None,
            "execution_error": None,
            "summary": None,
            "insights": [],
            "status": "processing",
            "error_message": None,
        }

        # Run multi-agent state graph
        final_state: AgentState = await nl2db_graph.ainvoke(initial_state)

        # Extract execution output
        exec_res = final_state.get("execution_result") or {}
        rows = exec_res.get("rows", [])
        columns = exec_res.get("columns", [])
        row_count = exec_res.get("row_count", len(rows))
        exec_time = exec_res.get("execution_time_ms", 0.0)

        # Determine overall user-facing status
        status = final_state.get("status", "success")
        if status == "processing":
            status = "success" if final_state.get("execution_result") else "error"

        return {
            "query_id": query_id,
            "status": status,
            "database_type": final_state["database_type"],
            "connector_id": connector_id,
            "user_prompt": user_prompt,
            "generated_query": final_state.get("generated_query"),
            "query_explanation": final_state.get("query_explanation"),
            "is_valid": final_state.get("is_valid", False),
            "retry_count": final_state.get("retry_count", 0),
            "columns": columns,
            "rows": rows,
            "row_count": row_count,
            "execution_time_ms": exec_time,
            "summary": final_state.get("summary"),
            "insights": final_state.get("insights", []),
            "error_message": final_state.get("error_message") or final_state.get("validation_error") or final_state.get("execution_error"),
        }


_service_instance: Optional[NL2DBService] = None


def get_nl2db_service() -> NL2DBService:
    global _service_instance
    if _service_instance is None:
        _service_instance = NL2DBService()
    return _service_instance
