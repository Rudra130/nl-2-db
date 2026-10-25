"""Deterministic Mock LLM Client for offline testing and local development."""
import json
import re
from typing import Any, Dict, List, Optional
from backend.app.config import Settings, get_settings


class MockLLMClient:
    """Mock LLM engine that returns context-aware deterministic responses."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        data = await self.generate_json(prompt, system_prompt=system_prompt)
        return json.dumps(data)

    async def generate_json(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        prompt_lower = prompt.lower()

        # 1. Intent Classification
        if "intent classification agent" in prompt_lower:
            return self._handle_intent(prompt_lower)

        # 2. Schema Pruning / Selection
        if "schema pruning agent" in prompt_lower:
            return self._handle_schema_pruning(prompt_lower)

        # 3. Error Recovery
        if "error recovery agent" in prompt_lower:
            return self._handle_recovery(prompt_lower)

        # 4. Result Summarization
        if "result interpretation" in prompt_lower:
            return self._handle_summary(prompt_lower)

        # 5. MongoDB Query Generation
        if "mongodb query generation agent" in prompt_lower or "target database: mongodb" in prompt_lower:
            return self._handle_mongodb_generation(prompt_lower)

        # 6. SQL Query Generation
        return self._handle_sql_generation(prompt_lower)

    def _handle_intent(self, prompt: str) -> Dict[str, Any]:
        req_match = re.search(r'user (?:request|question):\s*"([^"]+)"', prompt, re.IGNORECASE)
        user_req = req_match.group(1).lower() if req_match else prompt.lower()

        # Malicious / Write intent checks strictly on user input
        if any(w in user_req for w in [
            "delete", "remove", "drop", "truncate", "purge", "erase", "destroy",
            "insert", "add new", "add a new", "create new", "create a new", "create table",
            "update", "modify", "alter", "change the status", "change the price", "upgrade customer",
        ]):
            return {
                "intent": "unsupported_write",
                "reasoning": "Mutation operation (DELETE/UPDATE/INSERT/DROP) is strictly prohibited. Only read-only queries are supported.",
                "is_safe": False,
            }
        if any(w in user_req for w in ["password", ".env", "credential", "hack", "system escape", "admin pass", "sleep("]):
            return {
                "intent": "malicious",
                "reasoning": "Security breach attempt or unauthorized access to system credentials.",
                "is_safe": False,
            }
        if any(w in user_req for w in ["what tables", "show schema", "list collections", "describe database"]):
            return {
                "intent": "schema_inquiry",
                "reasoning": "Inquiry regarding database structure and schemas.",
                "is_safe": True,
            }

        return {
            "intent": "data_query",
            "reasoning": "Valid analytical read-only data request.",
            "is_safe": True,
        }

    @staticmethod
    def _extract_user_prompt(prompt: str) -> str:
        req_match = re.search(r'user (?:question|prompt|request):\s*"([^"]+)"', prompt, re.IGNORECASE)
        if req_match:
            return req_match.group(1).lower().strip()
        return prompt.lower().strip()

    def _handle_schema_pruning(self, prompt: str) -> Dict[str, Any]:
        user_q = self._extract_user_prompt(prompt)
        selected = []
        if any(w in user_q for w in ["customer", "user", "client", "tier", "gold", "platinum", "silver", "bronze"]):
            selected.append("customers")
        if any(w in user_q for w in ["product", "item", "stock", "price", "expensive"]):
            selected.append("products")
        if any(w in user_q for w in ["order", "sale", "revenue", "spend", "purchas", "delivered"]):
            selected.append("orders")
            selected.append("order_items")
        if any(w in user_q for w in ["category", "categories"]):
            selected.append("categories")

        if not selected:
            selected = ["products", "orders", "customers"]

        return {
            "selected_tables": list(set(selected)),
            "reasoning": "Selected tables correlated with question keywords.",
        }

    def _handle_sql_generation(self, prompt: str) -> Dict[str, Any]:
        user_q = self._extract_user_prompt(prompt)

        # 1. Customer tier queries ("gold", "platinum", "silver", "bronze", "tier")
        if any(w in user_q for w in ["gold", "platinum", "silver", "bronze", "tier"]):
            if "gold" in user_q and "platinum" in user_q:
                condition = "LOWER(tier) IN ('gold', 'platinum')"
                expl = "Retrieves all customers with gold or platinum membership tiers."
            elif "gold" in user_q:
                condition = "LOWER(tier) = 'gold'"
                expl = "Retrieves all customers with gold membership tier."
            elif "platinum" in user_q:
                condition = "LOWER(tier) = 'platinum'"
                expl = "Retrieves all customers with platinum membership tier."
            elif "silver" in user_q:
                condition = "LOWER(tier) = 'silver'"
                expl = "Retrieves all customers with silver membership tier."
            else:
                condition = "tier IS NOT NULL"
                expl = "Retrieves customers and their membership tiers."

            return {
                "query": f"SELECT id, name, email, tier, created_at FROM customers WHERE {condition} ORDER BY id ASC LIMIT 50",
                "explanation": expl,
                "tables_used": ["customers"],
            }

        # 2. Stock levels ("stock", "less than", "greater than", "inventory")
        if "stock" in user_q:
            num_match = re.search(r'\b(\d+)\b', user_q)
            threshold = num_match.group(1) if num_match else "50"
            op = "<" if any(w in user_q for w in ["less", "under", "fewer", "below", "low"]) else ">"
            return {
                "query": f"SELECT id, name, price, stock FROM products WHERE stock {op} {threshold} ORDER BY stock ASC LIMIT 50",
                "explanation": f"Filters product catalog for stock {op} {threshold} units.",
                "tables_used": ["products"],
            }

        # 3. Most expensive products
        if "expensive" in user_q or ("top" in user_q and ("product" in user_q or "price" in user_q)):
            num_match = re.search(r'top\s+(\d+)', user_q)
            limit = num_match.group(1) if num_match else "5"
            return {
                "query": f"SELECT id, name, price, stock FROM products ORDER BY price DESC LIMIT {limit}",
                "explanation": f"Retrieves the top {limit} most expensive products sorted in descending order of price.",
                "tables_used": ["products"],
            }

        # 4. Customer revenue / total spend
        if "revenue" in user_q or "spent" in user_q or "spend" in user_q:
            return {
                "query": (
                    "SELECT c.id, c.name, c.tier, COUNT(o.id) AS total_orders, "
                    "COALESCE(SUM(o.total_amount), 0) AS total_revenue "
                    "FROM customers c "
                    "LEFT JOIN orders o ON c.id = o.customer_id "
                    "GROUP BY c.id, c.name, c.tier "
                    "ORDER BY total_revenue DESC LIMIT 50"
                ),
                "explanation": "Aggregates total orders and revenue generated by each customer using a LEFT JOIN.",
                "tables_used": ["customers", "orders"],
            }

        # 5. Customer with highest number of orders
        if "highest" in user_q and "order" in user_q:
            return {
                "query": (
                    "SELECT c.id, c.name, c.tier, COUNT(o.id) AS total_orders "
                    "FROM customers c "
                    "JOIN orders o ON c.id = o.customer_id "
                    "GROUP BY c.id, c.name, c.tier "
                    "ORDER BY total_orders DESC LIMIT 1"
                ),
                "explanation": "Calculates customer with the highest order volume.",
                "tables_used": ["customers", "orders"],
            }

        # 6. Categories & Product Count / Average price
        if "categor" in user_q:
            return {
                "query": (
                    "SELECT c.name AS category_name, COUNT(p.id) AS product_count, COALESCE(AVG(p.price), 0) AS avg_price "
                    "FROM categories c "
                    "LEFT JOIN products p ON c.id = p.category_id "
                    "GROUP BY c.id, c.name "
                    "ORDER BY product_count DESC"
                ),
                "explanation": "Calculates the total products and average price per category.",
                "tables_used": ["categories", "products"],
            }

        # 7. Recent orders / Delivered orders
        if "order" in user_q:
            where_clause = "WHERE o.status = 'delivered' " if "delivered" in user_q else ""
            return {
                "query": (
                    f"SELECT o.id, c.name AS customer_name, o.order_date, o.status, o.total_amount "
                    f"FROM orders o "
                    f"JOIN customers c ON o.customer_id = c.id "
                    f"{where_clause}"
                    f"ORDER BY o.order_date DESC LIMIT 10"
                ),
                "explanation": "Retrieves recent orders with associated customer names.",
                "tables_used": ["orders", "customers"],
            }

        # 8. General customer query
        if "customer" in user_q or "user" in user_q or "client" in user_q:
            return {
                "query": "SELECT id, name, email, tier, created_at FROM customers ORDER BY created_at DESC LIMIT 50",
                "explanation": "Lists customers with account status and email address.",
                "tables_used": ["customers"],
            }

        # Fallback products query
        return {
            "query": "SELECT id, name, price, stock FROM products ORDER BY id ASC LIMIT 50",
            "explanation": "Default retrieval of available product inventory.",
            "tables_used": ["products"],
        }

    def _handle_mongodb_generation(self, prompt: str) -> Dict[str, Any]:
        user_q = self._extract_user_prompt(prompt)

        # 1. Customer tier queries
        if any(w in user_q for w in ["gold", "platinum", "silver", "bronze", "tier"]):
            tiers = []
            if "gold" in user_q: tiers.append("gold")
            if "platinum" in user_q: tiers.append("platinum")
            if "silver" in user_q: tiers.append("silver")
            if "bronze" in user_q: tiers.append("bronze")
            flt = {"tier": {"$in": tiers}} if tiers else {}
            return {
                "collection": "customers",
                "operation": "find",
                "query": {"filter": flt, "limit": 50},
                "explanation": f"Filters customers by tiers: {tiers or 'all'}.",
                "tables_used": ["customers"],
            }

        # 2. Stock levels
        if "stock" in user_q:
            num_match = re.search(r'\b(\d+)\b', user_q)
            val = int(num_match.group(1)) if num_match else 50
            op = "$lt" if any(w in user_q for w in ["less", "under", "fewer", "below", "low"]) else "$gt"
            return {
                "collection": "products",
                "operation": "find",
                "query": {"filter": {"stock": {op: val}}, "sort": {"stock": 1}, "limit": 50},
                "explanation": f"Filters products with stock {op} {val}.",
                "tables_used": ["products"],
            }

        # 3. Revenue / Total spent
        if "revenue" in user_q or "spent" in user_q or "spend" in user_q:
            return {
                "collection": "orders",
                "operation": "aggregate",
                "query": {
                    "pipeline": [
                        {"$group": {"_id": "$customer_id", "total_spent": {"$sum": "$total_amount"}, "order_count": {"$sum": 1}}},
                        {"$sort": {"total_spent": -1}},
                        {"$limit": 10}
                    ]
                },
                "explanation": "Aggregates total spent and order counts per customer from the orders collection.",
                "tables_used": ["orders"],
            }

        # 4. Most expensive products
        if "expensive" in user_q or "price" in user_q:
            num_match = re.search(r'top\s+(\d+)', user_q)
            limit = int(num_match.group(1)) if num_match else 5
            return {
                "collection": "products",
                "operation": "find",
                "query": {"filter": {}, "sort": {"price": -1}, "limit": limit},
                "explanation": f"Finds top {limit} products sorted descending by price.",
                "tables_used": ["products"],
            }

        # 5. Orders / Delivered
        if "order" in user_q:
            flt = {"status": "delivered"} if "delivered" in user_q else {}
            return {
                "collection": "orders",
                "operation": "find",
                "query": {"filter": flt, "sort": {"order_date": -1}, "limit": 10},
                "explanation": "Finds orders sorted descending by order date.",
                "tables_used": ["orders"],
            }

        # Default customers
        return {
            "collection": "customers",
            "operation": "find",
            "query": {"filter": {}, "limit": 50},
            "explanation": "Retrieves customer records from the customers collection.",
            "tables_used": ["customers"],
        }

    def _handle_recovery(self, prompt: str) -> Dict[str, Any]:
        return {
            "query": "SELECT id, name, price, stock FROM products LIMIT 10",
            "explanation": "Sanitized safe fallback query conforming to read-only constraints.",
            "tables_used": ["products"],
        }

    def _handle_summary(self, prompt: str) -> Dict[str, Any]:
        user_q = self._extract_user_prompt(prompt)
        return {
            "summary": f"The query successfully executed, retrieving the requested records for '{user_q}'.",
            "insights": [
                "Results strictly match the requested filter criteria.",
                "Read-only execution verified by deterministic AST parsing."
            ]
        }
