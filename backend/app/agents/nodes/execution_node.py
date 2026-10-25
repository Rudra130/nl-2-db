"""Safe Query Execution Agent Node."""
from backend.app.agents.state import AgentState
from backend.app.config import get_settings
from backend.app.connectors.registry import get_connector_registry


async def execution_node(state: AgentState) -> dict:
    settings = get_settings()
    registry = get_connector_registry()
    connector = registry.get_connector(state["connector_id"])

    try:
        res = await connector.execute_read_query(
            query=state["generated_query"],
            row_limit=settings.DEFAULT_ROW_LIMIT,
            timeout_seconds=settings.MAX_QUERY_TIMEOUT_SECONDS,
        )

        if not res.success:
            return {
                "execution_result": None,
                "execution_error": res.error or "Execution failed without details.",
            }

        return {
            "execution_result": res.model_dump(),
            "execution_error": None,
        }
    except Exception as e:
        return {
            "execution_result": None,
            "execution_error": f"Execution exception: {str(e)}",
        }
