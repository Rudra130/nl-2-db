"""Unit tests for AST deterministic SQL Validator."""
import pytest
from backend.app.security.sql_validator import validate_sql_query


def test_valid_select_query():
    sql = "SELECT id, name, price FROM products WHERE price > 100 ORDER BY price DESC"
    res = validate_sql_query(sql, dialect="sqlite")
    assert res.is_valid is True
    assert "products" in res.extracted_tables
    assert "LIMIT" in res.suggested_safe_query


def test_reject_mutation_queries():
    queries = [
        "DELETE FROM customers WHERE id = 1",
        "DROP TABLE products",
        "INSERT INTO categories (id, name, slug) VALUES (10, 'Toys', 'toys')",
        "UPDATE orders SET status = 'cancelled' WHERE id = 2",
        "TRUNCATE TABLE order_items",
        "ALTER TABLE customers ADD COLUMN balance INT",
    ]
    for q in queries:
        res = validate_sql_query(q, dialect="sqlite")
        assert res.is_valid is False
        assert "Prohibited" in res.error_message or "Read-only" in res.error_message


def test_reject_multistatement():
    sql = "SELECT * FROM customers; DROP TABLE orders;"
    res = validate_sql_query(sql, dialect="sqlite")
    assert res.is_valid is False
    assert any(term in res.error_message.lower() for term in ["multi-statement", "single-statement", "prohibited"])


def test_table_whitelist_enforcement():
    sql = "SELECT * FROM secret_passwords"
    res = validate_sql_query(
        sql,
        dialect="sqlite",
        allowed_tables={"products", "customers"},
    )
    assert res.is_valid is False
    assert "secret_passwords" in res.error_message


def test_prohibited_dangerous_functions():
    sql = "SELECT SLEEP(10) FROM products"
    res = validate_sql_query(sql, dialect="mysql")
    assert res.is_valid is False
    assert "sleep" in res.error_message.lower()
