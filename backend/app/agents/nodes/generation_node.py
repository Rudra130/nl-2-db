"""Query Generation Agent Node (NVIDIA NIM Prompt Engine)."""
import json
from backend.app.agents.state import AgentState
from backend.app.config import get_settings
from backend.app.connectors.registry import get_connector_registry
from backend.app.llm import get_llm_client
from backend.app.llm.template_engine import render_prompt


async def generation_node(state: AgentState) -> dict:
    settings = get_settings()
    registry = get_connector_registry()
    cap = registry.get_capability(state["database_type"])
    client = get_llm_client()

    if cap.is_sql:
        prompt = render_prompt(
            "sql_gen.j2",
            dialect=cap.dialect,
            schema_context=state["schema_summary"],
            user_prompt=state["user_prompt"],
            default_limit=settings.DEFAULT_ROW_LIMIT,
            hard_max_rows=settings.HARD_MAX_ROWS,
        )
    else:
        prompt = render_prompt(
            "nosql_gen.j2",
            schema_context=state["schema_summary"],
            user_prompt=state["user_prompt"],
            default_limit=settings.DEFAULT_ROW_LIMIT,
            hard_max_rows=settings.HARD_MAX_ROWS,
        )

    try:
        res = await client.generate_json(prompt)

        if cap.is_sql:
            query = res.get("query", "").strip()
        else:
            # For MongoDB, format as JSON string with collection and operation
            query_obj = {
                "collection": res.get("collection", ""),
                "operation": res.get("operation", "find"),
                "query": res.get("query", {}),
            }
            query = json.dumps(query_obj)

        explanation = res.get("explanation", "")
        return {
            "generated_query": query,
            "query_explanation": explanation,
        }
    except Exception as e:
        return {
            "generated_query": "",
            "query_explanation": f"Generation failed: {str(e)}",
            "is_valid": False,
            "validation_error": str(e),
        }
