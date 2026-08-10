from fastapi import APIRouter
from app.config import settings
from app.rag.vector_store import vector_rag

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "commit": "d3b10a0",
        "environment": settings.ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "demo_mode": settings.DEMO_MODE,
        "rag_status": "active"
    }
