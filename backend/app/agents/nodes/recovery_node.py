"""Error Recovery Agent Node (Bounded Self-Correction)."""
from backend.app.agents.state import AgentState
from backend.app.config import get_settings
from backend.app.connectors.registry import get_connector_registry
from backend.app.llm import get_llm_client
from backend.app.llm.template_engine import render_prompt


async def recovery_node(state: AgentState) -> dict:
    settings = get_settings()
    current_retry = state.get("retry_count", 0) + 1
    error_diag = state.get("validation_error") or state.get("execution_error") or "Unknown error"

    if current_retry > settings.MAX_RECOVERY_RETRIES:
        return {
            "retry_count": current_retry,
            "status": "rejected",
            "error_message": f"Query recovery retries exhausted ({settings.MAX_RECOVERY_RETRIES} attempts). Last error: {error_diag}",
        }

    registry = get_connector_registry()
    cap = registry.get_capability(state["database_type"])
    client = get_llm_client()

    prompt = render_prompt(
        "recovery.j2",
        database_type=state["database_type"],
        dialect=cap.dialect,
        schema_context=state["schema_summary"],
        user_prompt=state["user_prompt"],
        failed_query=state.get("generated_query", ""),
        error_message=error_diag,
    )

    try:
        res = await client.generate_json(prompt)
        corrected_query = res.get("query", "")
        if isinstance(corrected_query, dict):
            import json
            corrected_query = json.dumps(corrected_query)

        return {
            "retry_count": current_retry,
            "generated_query": str(corrected_query).strip(),
            "query_explanation": res.get("explanation", "Corrected based on diagnostic feedback."),
            "validation_error": None,
            "execution_error": None,
        }
    except Exception as e:
        return {
            "retry_count": current_retry,
            "status": "error",
            "error_message": f"Recovery attempt failed: {str(e)}",
        }
