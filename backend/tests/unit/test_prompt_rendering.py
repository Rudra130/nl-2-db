"""Unit tests for Jinja2 Prompt Templates."""
from backend.app.llm.template_engine import render_prompt


def test_intent_prompt_rendering():
    p = render_prompt("intent.j2", user_prompt="Show top 5 products")
    assert "Show top 5 products" in p
    assert "Intent Classification Agent" in p


def test_sql_gen_prompt_rendering():
    p = render_prompt(
        "sql_gen.j2",
        dialect="sqlite",
        schema_context="Table `products`: id, name, price",
        user_prompt="List all products",
        default_limit=50,
        hard_max_rows=500,
    )
    assert "sqlite" in p
    assert "Table `products`" in p
    assert "List all products" in p
