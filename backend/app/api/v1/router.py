from fastapi import APIRouter
from app.api.v1.fact_check import router as fact_check_router
from app.api.v1.health import router as health_router
from app.api.v1.evaluation import router as evaluation_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(fact_check_router)
api_v1_router.include_router(evaluation_router)
