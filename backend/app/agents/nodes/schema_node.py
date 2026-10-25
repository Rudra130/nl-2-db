"""Schema Selection and Discovery Agent Node."""
from backend.app.agents.state import AgentState
from backend.app.connectors.registry import get_connector_registry
from backend.app.schema.introspector import get_schema_introspector
from backend.app.llm import get_llm_client
from backend.app.llm.template_engine import render_prompt


async def schema_node(state: AgentState) -> dict:
    registry = get_connector_registry()
    connector = registry.get_connector(state["connector_id"])
    introspector = get_schema_introspector()

    # Discover full schema from connector
    full_schema = await introspector.get_schema(connector)
    table_names = full_schema.get_table_names()

    # If small schema (<= 5 tables), use all tables directly to save latency
    if len(table_names) <= 5:
        summary = introspector.format_for_prompt(full_schema)
        return {
            "selected_tables": table_names,
            "schema_summary": summary,
        }

    # Otherwise prune with LLM
    client = get_llm_client()
    summary_all = introspector.format_for_prompt(full_schema)
    prompt = render_prompt(
        "schema_filter.j2",
        database_type=state["database_type"],
        schema_summary=summary_all,
        user_prompt=state["user_prompt"],
    )

    try:
        res = await client.generate_json(prompt)
        selected = res.get("selected_tables", table_names)
        # Fallback if empty
        if not selected:
            selected = table_names
    except Exception:
        selected = table_names

    pruned_summary = introspector.format_for_prompt(full_schema, selected)
    return {
        "selected_tables": selected,
        "schema_summary": pruned_summary,
    }
