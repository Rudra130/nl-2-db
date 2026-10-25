"""Query Execution API Endpoint."""
from fastapi import APIRouter, HTTPException
from backend.app.api.models.query import QueryRequest, QueryResponse
from backend.app.services.nl2db_service import get_nl2db_service

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("", response_model=QueryResponse)
async def execute_natural_language_query(request: QueryRequest):
    """Process natural language request through the LangGraph multi-agent pipeline."""
    service = get_nl2db_service()
    try:
        result = await service.execute_query(
            user_prompt=request.prompt,
            connector_id=request.connector_id,
        )
        return QueryResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query pipeline error: {str(e)}")
