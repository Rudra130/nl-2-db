"""Execution Limits and Guardrails."""
import asyncio
from typing import Any, Callable, Coroutine, TypeVar

T = TypeVar("T")


class QueryTimeoutError(Exception):
    """Raised when query execution exceeds the allowed execution time limit."""
    pass


class RowLimitExceededError(Exception):
    """Raised when query results exceed system-enforced maximum row limit."""
    pass


async def run_with_timeout(
    coro: Coroutine[Any, Any, T],
    timeout_seconds: float,
    operation_name: str = "Query"
) -> T:
    """Run an async coroutine with a strict timeout limit."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        raise QueryTimeoutError(
            f"{operation_name} execution timed out after {timeout_seconds} seconds. "
            f"Please refine your query to narrow down the data range."
        )


def enforce_row_limits(
    rows: list[Any],
    hard_max: int = 500,
    requested_limit: int | None = None
) -> tuple[list[Any], bool]:
    """
    Ensure the returned row count does not exceed hard bounds.
    Returns (sliced_rows, was_truncated).
    """
    max_allowed = min(requested_limit or hard_max, hard_max)
    if len(rows) > max_allowed:
        return rows[:max_allowed], True
    return rows, False
