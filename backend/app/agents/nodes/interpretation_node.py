"""Result Interpretation and Summarization Agent Node."""
from backend.app.agents.state import AgentState
from backend.app.llm import get_llm_client
from backend.app.llm.template_engine import render_prompt


async def interpretation_node(state: AgentState) -> dict:
    exec_res = state.get("execution_result") or {}
    rows = exec_res.get("rows", [])
    row_count = exec_res.get("row_count", len(rows))
    exec_time = exec_res.get("execution_time_ms", 0.0)

    if not rows:
        return {
            "summary": "The query executed successfully, but returned no matching records for the specified criteria.",
            "insights": ["0 rows returned.", "Verify filter parameters or data availability."],
            "status": "success",
        }

    # Pass at most 5 sample rows to keep prompt concise
    sample = rows[:5]
    client = get_llm_client()
    prompt = render_prompt(
        "summary.j2",
        user_prompt=state["user_prompt"],
        executed_query=state.get("generated_query", ""),
        row_count=row_count,
        execution_time_ms=exec_time,
        sample_rows=sample,
    )

    try:
        res = await client.generate_json(prompt)
        return {
            "summary": res.get("summary", f"Successfully retrieved {row_count} records."),
            "insights": res.get("insights", [f"Query returned {row_count} rows in {exec_time:.2f}ms."]),
            "status": "success",
        }
    except Exception:
        return {
            "summary": f"Query returned {row_count} records successfully.",
            "insights": [f"Returned {row_count} rows in {exec_time:.2f}ms."],
            "status": "success",
        }
