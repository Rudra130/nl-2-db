"""Health and Readiness Probes."""
from fastapi import APIRouter
from backend.app.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    settings = get_settings()
    return {
        "status": "healthy",
        "service": "NL2DB Query Platform",
        "environment": settings.ENVIRONMENT,
        "llm_mode": "mock" if (settings.USE_MOCK_LLM or not settings.NVIDIA_NIM_API_KEY) else "nvidia_nim",
        "model": settings.NVIDIA_NIM_MODEL,
    }
