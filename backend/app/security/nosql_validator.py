"""MongoDB Query and Aggregation Pipeline Validator."""
import json
from typing import Any, Dict, List, Set
from pydantic import BaseModel, Field


class NoSQLValidationResult(BaseModel):
    is_valid: bool
    error_message: str | None = None
    collection: str | None = None
    operation: str = "find"
    parsed_query: Dict[str, Any] = Field(default_factory=dict)
    extracted_collections: List[str] = Field(default_factory=list)


ALLOWED_OPERATIONS: Set[str] = {"find", "aggregate", "countDocuments", "distinct"}

# Stages that can write to database or execute arbitrary JavaScript
PROHIBITED_STAGES: Set[str] = {
    "$out",
    "$merge",
    "$accumulator",
    "$function",
    "$planCacheStats",
}

# Dangerous operators that execute JS or attempt mutations
PROHIBITED_OPERATORS: Set[str] = {
    "$where",
    "$rename",
    "$set",
    "$unset",
    "$inc",
    "$push",
    "$pull",
    "$pop",
    "$mul",
    "$min",
    "$max",
    "$currentDate",
    "$bit",
}


def _check_dict_for_prohibited_operators(d: Any) -> str | None:
    """Recursively check dictionary for prohibited operators like $where."""
    if isinstance(d, dict):
        for k, v in d.items():
            if str(k).lower() in PROHIBITED_OPERATORS:
                return f"Prohibited operator '{k}' is not allowed in read-only queries."
            err = _check_dict_for_prohibited_operators(v)
            if err:
                return err
    elif isinstance(d, list):
        for item in d:
            err = _check_dict_for_prohibited_operators(item)
            if err:
                return err
    return None


def validate_mongodb_query(
    query_input: str | dict,
    allowed_collections: set[str] | None = None,
    default_limit: int = 50,
) -> NoSQLValidationResult:
    """
    Validate a MongoDB query representation against strict read-only rules.
    Expected format:
    {
       "collection": "orders",
       "operation": "find" | "aggregate" | "countDocuments",
       "filter": { ... },
       "pipeline": [ ... ],
       "limit": 50
    }
    """
    if isinstance(query_input, str):
        try:
            query_obj = json.loads(query_input)
        except Exception as e:
            return NoSQLValidationResult(
                is_valid=False,
                error_message=f"MongoDB query must be a valid JSON object: {str(e)}",
            )
    elif isinstance(query_input, dict):
        query_obj = query_input
    else:
        return NoSQLValidationResult(
            is_valid=False,
            error_message="Query input must be a JSON string or dictionary.",
        )

    # 1. Collection check
    collection = query_obj.get("collection")
    if not collection or not isinstance(collection, str):
        return NoSQLValidationResult(
            is_valid=False,
            error_message="Query must specify a target 'collection' name.",
        )

    if allowed_collections:
        allowed_lower = {c.lower() for c in allowed_collections}
        if collection.lower() not in allowed_lower:
            return NoSQLValidationResult(
                is_valid=False,
                collection=collection,
                error_message=f"Access denied to collection '{collection}'. Allowed collections: {', '.join(sorted(allowed_collections))}.",
            )

    # 2. Operation check
    operation = query_obj.get("operation", "find")
    if operation not in ALLOWED_OPERATIONS:
        return NoSQLValidationResult(
            is_valid=False,
            collection=collection,
            error_message=f"Prohibited operation '{operation}'. Allowed read operations: {', '.join(sorted(ALLOWED_OPERATIONS))}.",
        )

    # Support both flat and nested 'query' structure
    inner_query = query_obj.get("query") if isinstance(query_obj.get("query"), dict) else {}

    # Check for prohibited operators in whole query object
    err = _check_dict_for_prohibited_operators(query_obj)
    if err:
        return NoSQLValidationResult(is_valid=False, collection=collection, error_message=err)

    # 4. Aggregation pipeline checks
    if operation == "aggregate":
        pipeline = query_obj.get("pipeline") or inner_query.get("pipeline")
        if not isinstance(pipeline, list):
            return NoSQLValidationResult(
                is_valid=False,
                collection=collection,
                error_message="Aggregation requires a 'pipeline' array of stage objects.",
            )

        has_limit = False
        for idx, stage in enumerate(pipeline):
            if not isinstance(stage, dict):
                return NoSQLValidationResult(
                    is_valid=False,
                    collection=collection,
                    error_message=f"Pipeline stage {idx} must be a dictionary.",
                )

            for stage_name in stage.keys():
                if stage_name in PROHIBITED_STAGES:
                    return NoSQLValidationResult(
                        is_valid=False,
                        collection=collection,
                        error_message=f"Prohibited aggregation stage '{stage_name}' detected. Aggregation must not write data.",
                    )
                if stage_name == "$limit":
                    has_limit = True

            err = _check_dict_for_prohibited_operators(stage)
            if err:
                return NoSQLValidationResult(is_valid=False, collection=collection, error_message=err)

        # Enforce safe limit on pipeline if missing
        if not has_limit:
            pipeline.append({"$limit": default_limit})

        if "pipeline" in query_obj:
            query_obj["pipeline"] = pipeline
        elif "query" in query_obj and isinstance(query_obj["query"], dict):
            query_obj["query"]["pipeline"] = pipeline

    elif operation == "find":
        target_dict = query_obj if "limit" in query_obj or "query" not in query_obj else inner_query
        if "limit" not in target_dict or not isinstance(target_dict["limit"], int):
            target_dict["limit"] = default_limit
        elif target_dict["limit"] > default_limit:
            target_dict["limit"] = default_limit

    return NoSQLValidationResult(
        is_valid=True,
        collection=collection,
        operation=operation,
        parsed_query=query_obj,
        extracted_collections=[collection],
    )
