"""Deterministic SQL Query Validator using sqlglot AST parsing."""
from typing import Set, Tuple
import sqlglot
from sqlglot import exp
from pydantic import BaseModel, Field


class SQLValidationResult(BaseModel):
    is_valid: bool
    error_message: str | None = None
    dialect: str = "generic"
    extracted_tables: list[str] = Field(default_factory=list)
    extracted_columns: list[str] = Field(default_factory=list)
    has_limit: bool = False
    suggested_safe_query: str | None = None


# Expressions that modify schema or data, or trigger administrative actions
PROHIBITED_EXPRESSIONS: Tuple[type, ...] = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.Command,
    exp.TruncateTable,
    exp.Merge,
    exp.Grant,
    exp.Revoke,
    exp.Transaction,
    exp.Commit,
    exp.Rollback,
    exp.Set,
    exp.Pragma,
    exp.Into,  # INTO OUTFILE / DUMPFILE
)

# Functions known to cause denial-of-service, sleep, or file system access
PROHIBITED_FUNCTIONS: Set[str] = {
    "sleep",
    "pg_sleep",
    "benchmark",
    "load_file",
    "sys_exec",
    "xp_cmdshell",
    "pg_read_file",
    "pg_write_file",
    "version",
    "database",
    "current_user",
    "system_user",
}


def validate_sql_query(
    sql: str,
    dialect: str = "mysql",
    allowed_tables: set[str] | None = None,
    enforce_limit: bool = True,
    default_limit: int = 50,
) -> SQLValidationResult:
    """
    Deterministically validate a SQL query using AST parsing.
    
    Guarantees:
    1. Single-statement only (multi-statements rejected).
    2. Read-only operation only (SELECT or read-only WITH CTE).
    3. No DDL, DML, administrative commands, or system-compromising functions.
    4. Table whitelisting against discovered schema (if allowed_tables provided).
    5. Automatic safe LIMIT injection if missing and enforce_limit is True.
    """
    cleaned_sql = sql.strip()
    if not cleaned_sql:
        return SQLValidationResult(is_valid=False, error_message="Query cannot be empty.")

    # 1. Parse into AST
    dialect_map = {
        "mysql": "mysql",
        "postgres": "postgres",
        "postgresql": "postgres",
        "sqlite": "sqlite",
    }
    target_dialect = dialect_map.get(dialect.lower(), "mysql")

    try:
        parsed_statements = sqlglot.parse(cleaned_sql, read=target_dialect)
    except Exception as e:
        return SQLValidationResult(
            is_valid=False,
            dialect=target_dialect,
            error_message=f"SQL syntax error or invalid dialect syntax: {str(e)}",
        )

    # 2. Reject multi-statement queries
    if len(parsed_statements) == 0:
        return SQLValidationResult(is_valid=False, dialect=target_dialect, error_message="No valid SQL statements found.")
    
    if len(parsed_statements) > 1:
        return SQLValidationResult(
            is_valid=False,
            dialect=target_dialect,
            error_message="Multi-statement SQL queries are strictly prohibited for security.",
        )

    ast = parsed_statements[0]
    if ast is None:
        return SQLValidationResult(is_valid=False, dialect=target_dialect, error_message="Failed to parse statement AST.")

    # 3. Enforce statement root type: Must be Select or With (CTEs)
    if not isinstance(ast, (exp.Select, exp.Union)):
        return SQLValidationResult(
            is_valid=False,
            dialect=target_dialect,
            error_message=f"Prohibited operation: Only SELECT queries are permitted (received {ast.key.upper()}).",
        )

    # 4. Check for any nested prohibited expressions anywhere in the AST
    for prohibited in PROHIBITED_EXPRESSIONS:
        found = list(ast.find_all(prohibited))
        if found:
            return SQLValidationResult(
                is_valid=False,
                dialect=target_dialect,
                error_message=f"Prohibited operation detected: {prohibited.__name__} is not allowed in read-only queries.",
            )

    # 5. Check for prohibited function calls (e.g. sleep, benchmark)
    for func in ast.find_all(exp.Anonymous):
        func_name = func.this.lower() if isinstance(func.this, str) else ""
        if func_name in PROHIBITED_FUNCTIONS:
            return SQLValidationResult(
                is_valid=False,
                dialect=target_dialect,
                error_message=f"Prohibited function detected: '{func_name}' is not allowed.",
            )

    # 6. Extract CTE names so local aliases are not flagged as external tables
    cte_names = {cte.alias_or_name.lower() for cte in ast.find_all(exp.CTE) if cte.alias_or_name}

    # Extract tables and verify against allowed_tables if provided
    extracted_tables = []
    for table_expr in ast.find_all(exp.Table):
        t_name = table_expr.name
        if t_name and t_name not in extracted_tables:
            extracted_tables.append(t_name)

    if allowed_tables:
        allowed_lower = {t.lower() for t in allowed_tables}
        for tbl in extracted_tables:
            if tbl.lower() in cte_names:
                continue
            if tbl.lower() not in allowed_lower:
                return SQLValidationResult(
                    is_valid=False,
                    dialect=target_dialect,
                    extracted_tables=extracted_tables,
                    error_message=f"Access denied to unauthorized or unknown table '{tbl}'. Allowed tables: {', '.join(sorted(allowed_tables))}.",
                )

    # 7. Extract column references (for inspection/logging)
    extracted_columns = []
    for col_expr in ast.find_all(exp.Column):
        col_name = col_expr.name
        if col_name and col_name not in extracted_columns:
            extracted_columns.append(col_name)

    # 8. Check for LIMIT and optionally append if absent
    has_limit = ast.args.get("limit") is not None
    suggested_safe_query = cleaned_sql

    if not has_limit and enforce_limit:
        # Clone AST and append limit
        try:
            limited_ast = ast.limit(default_limit)
            suggested_safe_query = limited_ast.sql(dialect=target_dialect)
        except Exception:
            suggested_safe_query = f"{cleaned_sql} LIMIT {default_limit}"

    return SQLValidationResult(
        is_valid=True,
        dialect=target_dialect,
        extracted_tables=extracted_tables,
        extracted_columns=extracted_columns,
        has_limit=has_limit,
        suggested_safe_query=suggested_safe_query,
    )
