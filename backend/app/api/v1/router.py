"""V1 API Router Aggregator."""
from fastapi import APIRouter
from .health import router as health_router
from .connections import router as connections_router
from .query import router as query_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(health_router)
v1_router.include_router(connections_router)
v1_router.include_router(query_router)
