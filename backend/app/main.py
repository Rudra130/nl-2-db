"""FastAPI Application Main Entrypoint."""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import get_settings
from backend.app.connectors.registry import get_connector_registry
from backend.app.api.v1.router import v1_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure connections and introspectors ready
    yield
    # Shutdown: gracefully close connector pools
    registry = get_connector_registry()
    await registry.close_all()


settings = get_settings()

app = FastAPI(
    title="NL2DB Platform API",
    version="1.0.0",
    description="Natural Language to Database Query Platform with AST Validation and Agentic Orchestration",
    lifespan=lifespan,
)

# Configure CORS for Vite/React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(v1_router)


@app.get("/")
async def root():
    return {
        "title": "NL2DB Platform API",
        "version": "1.0.0",
        "documentation": "/docs",
        "status": "operational",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=True)
