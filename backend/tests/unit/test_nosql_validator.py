"""Unit tests for MongoDB NoSQL Validator."""
import json
import pytest
from backend.app.security.nosql_validator import validate_mongodb_query


def test_valid_find_query():
    query = {
        "collection": "products",
        "operation": "find",
        "query": {"filter": {"price": {"$gt": 100}}, "limit": 10},
    }
    res = validate_mongodb_query(query)
    assert res.is_valid is True
    assert res.collection == "products"


def test_valid_aggregate_pipeline():
    query = {
        "collection": "orders",
        "operation": "aggregate",
        "query": {
            "pipeline": [
                {"$match": {"status": "delivered"}},
                {"$group": {"_id": "$customer_id", "total": {"$sum": "$total_amount"}}},
                {"$limit": 5},
            ]
        },
    }
    res = validate_mongodb_query(query)
    assert res.is_valid is True


def test_prohibited_out_stage():
    query = {
        "collection": "orders",
        "operation": "aggregate",
        "query": {
            "pipeline": [
                {"$match": {"status": "delivered"}},
                {"$out": "backup_orders"},
            ]
        },
    }
    res = validate_mongodb_query(query)
    assert res.is_valid is False
    assert "$out" in res.error_message


def test_prohibited_where_operator():
    query = {
        "collection": "customers",
        "operation": "find",
        "query": {"filter": {"$where": "this.name.length > 5"}},
    }
    res = validate_mongodb_query(query)
    assert res.is_valid is False
    assert "$where" in res.error_message
