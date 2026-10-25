"""Deterministic Validation Agent Node (AST and Policy Enforcement)."""
import json
from backend.app.agents.state import AgentState
from backend.app.config import get_settings
from backend.app.connectors.registry import get_connector_registry
from backend.app.security.sql_validator import validate_sql_query
from backend.app.security.nosql_validator import validate_mongodb_query


async def validation_node(state: AgentState) -> dict:
    settings = get_settings()
    registry = get_connector_registry()
    cap = registry.get_capability(state["database_type"])
    raw_query = state.get("generated_query", "")

    if not raw_query or not raw_query.strip():
        return {
            "is_valid": False,
            "validation_error": "Generated query is empty.",
        }

    if cap.is_sql:
        result = validate_sql_query(
            sql=raw_query,
            dialect=cap.dialect,
            allowed_tables=set(state.get("selected_tables", [])) if state.get("selected_tables") else None,
            enforce_limit=True,
            default_limit=settings.DEFAULT_ROW_LIMIT,
        )

        safe_query = result.suggested_safe_query or raw_query
        return {
            "is_valid": result.is_valid,
            "validation_error": result.error_message,
            "generated_query": safe_query if result.is_valid else raw_query,
        }
    else:
        # MongoDB validation
        result = validate_mongodb_query(
            query_input=raw_query,
            allowed_collections=set(state.get("selected_tables", [])) if state.get("selected_tables") else None,
            default_limit=settings.DEFAULT_ROW_LIMIT,
        )

        formatted_query = json.dumps(result.parsed_query) if result.is_valid else raw_query
        return {
            "is_valid": result.is_valid,
            "validation_error": result.error_message,
            "generated_query": formatted_query,
        }
