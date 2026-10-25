"""LangGraph Multi-Agent Workflow State Machine."""
from typing import Literal
from langgraph.graph import StateGraph, START, END
from backend.app.config import get_settings
from backend.app.agents.state import AgentState
from backend.app.agents.nodes import (
    intent_node,
    schema_node,
    generation_node,
    validation_node,
    execution_node,
    recovery_node,
    interpretation_node,
)


def route_after_intent(state: AgentState) -> Literal["schema_node", "__end__"]:
    """Halt early if malicious, unsafe, or unauthorized write."""
    if state.get("status") in ["rejected", "error"] or not state.get("is_safe", True):
        return END
    return "schema_node"


def route_after_validation(state: AgentState) -> Literal["execution_node", "recovery_node", "__end__"]:
    """Route to execution if valid, or recovery if within retry budget."""
    settings = get_settings()
    if state.get("is_valid", False):
        return "execution_node"

    if state.get("retry_count", 0) < settings.MAX_RECOVERY_RETRIES:
        return "recovery_node"

    return END


def route_after_execution(state: AgentState) -> Literal["interpretation_node", "recovery_node", "__end__"]:
    """Route to interpretation if execution succeeded, or recovery if failed within retry budget."""
    settings = get_settings()
    if state.get("execution_result") is not None:
        return "interpretation_node"

    if state.get("retry_count", 0) < settings.MAX_RECOVERY_RETRIES:
        return "recovery_node"

    return END


def route_after_recovery(state: AgentState) -> Literal["validation_node", "__end__"]:
    """Route back to validation or terminate if budget exhausted."""
    if state.get("status") in ["rejected", "error"]:
        return END
    return "validation_node"


def build_nl2db_graph():
    """Construct and compile the deterministic LangGraph workflow."""
    workflow = StateGraph(AgentState)

    # Add all agent nodes
    workflow.add_node("intent_node", intent_node)
    workflow.add_node("schema_node", schema_node)
    workflow.add_node("generation_node", generation_node)
    workflow.add_node("validation_node", validation_node)
    workflow.add_node("execution_node", execution_node)
    workflow.add_node("recovery_node", recovery_node)
    workflow.add_node("interpretation_node", interpretation_node)

    # Connect workflow edges
    workflow.add_edge(START, "intent_node")

    workflow.add_conditional_edges(
        "intent_node",
        route_after_intent,
        {
            "schema_node": "schema_node",
            END: END,
        },
    )

    workflow.add_edge("schema_node", "generation_node")
    workflow.add_edge("generation_node", "validation_node")

    workflow.add_conditional_edges(
        "validation_node",
        route_after_validation,
        {
            "execution_node": "execution_node",
            "recovery_node": "recovery_node",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "execution_node",
        route_after_execution,
        {
            "interpretation_node": "interpretation_node",
            "recovery_node": "recovery_node",
            END: END,
        },
    )

    workflow.add_conditional_edges(
        "recovery_node",
        route_after_recovery,
        {
            "validation_node": "validation_node",
            END: END,
        },
    )

    workflow.add_edge("interpretation_node", END)

    return workflow.compile()


# Compiled singleton graph
nl2db_graph = build_nl2db_graph()
