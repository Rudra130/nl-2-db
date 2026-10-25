"""Intent Classification Agent Node with Deterministic Security Pre-checks."""
import re
from typing import Optional, Tuple
from backend.app.agents.state import AgentState
from backend.app.llm import get_llm_client
from backend.app.llm.template_engine import render_prompt

# Regex patterns for deterministic write / mutation detection
WRITE_PATTERNS = [
    (
        r"^\s*(?:please\s+)?(?:delete|remove|drop|truncate|purge|erase|destroy)\b",
        "DELETE / DROP operation is strictly forbidden. This platform enforces strict read-only analytical queries.",
    ),
    (
        r"\b(?:delete\s+(?:all|from|the|\d+|rows?|customers?|products?|orders?|categories?)|remove\s+(?:all|from|the|\d+|rows?|customers?|products?|orders?|categories?))\b",
        "DELETE / REMOVE operation is strictly forbidden. Write operations are blocked.",
    ),
    (
        r"\b(?:truncate|drop)\s+(?:table|database|collection|all)\b",
        "DDL TRUNCATE / DROP operation is strictly forbidden.",
    ),
    (
        r"^\s*(?:please\s+)?(?:insert|add|create)\s+(?:a\s+new|new|into|record|customer|product|order|category)\b",
        "INSERT / CREATE operation is strictly forbidden. This platform only allows read-only execution.",
    ),
    (
        r"\b(?:insert\s+into|insert\s+a\s+new|add\s+a\s+new|add\s+new\s+customer|add\s+new\s+product|add\s+new\s+order)\b",
        "INSERT operation is strictly forbidden.",
    ),
    (
        r"^\s*(?:please\s+)?(?:update|modify|alter|set|upgrade|change)\b.*?\b(?:to|status|price|tier|stock|=)\b",
        "UPDATE / MODIFY operation is strictly forbidden.",
    ),
    (
        r"\b(?:update\s+\w+\s+set|change\s+the\s+status|change\s+the\s+price|upgrade\s+customer|set\s+the\s+total)\b",
        "UPDATE operation is strictly forbidden.",
    ),
    (
        r"\b(?:alter\s+table|create\s+table|drop\s+table|create\s+index)\b",
        "DDL Schema modification is strictly forbidden.",
    ),
]

# Regex patterns for malicious injection or credential probes
MALICIOUS_PATTERNS = [
    (
        r"\b(?:password|passwords|\.env|credentials|secret_key|system\s+passwords?|root\s+passwords?)\b",
        "Security breach attempt: Access to system credentials, passwords, or environment variables is forbidden.",
    ),
    (
        r"\b(?:xp_cmdshell|exec\s+sp_|benchmark\s*\(|sleep\s*\()\b",
        "Dangerous system execution probe blocked.",
    ),
    (
        r";\s*(?:drop|delete|insert|update|alter|truncate)\b",
        "Multi-statement SQL injection payload blocked.",
    ),
]


def detect_unsafe_intent(prompt: str) -> Optional[Tuple[str, str]]:
    """Deterministically check if a prompt contains mutation or malicious instructions."""
    lower_prompt = prompt.lower().strip()

    # 1. Malicious check
    for pattern, reason in MALICIOUS_PATTERNS:
        if re.search(pattern, lower_prompt):
            return "malicious", reason

    # 2. Write check
    for pattern, reason in WRITE_PATTERNS:
        if re.search(pattern, lower_prompt):
            return "unsupported_write", reason

    return None


async def intent_node(state: AgentState) -> dict:
    user_prompt = state["user_prompt"]

    # 1. Deterministic Security Pre-filter (Defense-in-depth)
    pre_check = detect_unsafe_intent(user_prompt)
    if pre_check:
        intent_type, reason = pre_check
        return {
            "intent": intent_type,
            "is_safe": False,
            "intent_reasoning": reason,
            "status": "rejected",
            "error_message": f"Security Policy Blocked: {reason}",
        }

    # 2. LLM Intent Classification
    client = get_llm_client()
    prompt = render_prompt("intent.j2", user_prompt=user_prompt)

    try:
        res = await client.generate_json(prompt)
        intent = res.get("intent", "data_query")
        is_safe = res.get("is_safe", True)
        reasoning = res.get("reasoning", "")

        status = "processing"
        error_message = None

        if not is_safe or intent in ["unsupported_write", "malicious"]:
            status = "rejected"
            error_message = f"Security Policy Blocked: {reasoning or 'Non-read operation requested.'}"

        return {
            "intent": intent,
            "is_safe": is_safe,
            "intent_reasoning": reasoning,
            "status": status,
            "error_message": error_message,
        }
    except Exception as e:
        return {
            "intent": "ambiguous",
            "is_safe": False,
            "intent_reasoning": f"Intent error: {str(e)}",
            "status": "error",
            "error_message": f"Intent classification failure: {str(e)}",
        }
