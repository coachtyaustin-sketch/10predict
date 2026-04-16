from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.predictions import router as predictions_router
from app.api.signals import router as signals_router
from app.api.dashboard import router as dashboard_router
from app.api.research import router as research_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(predictions_router, prefix="/predictions", tags=["predictions"])
api_router.include_router(signals_router, prefix="/signals", tags=["signals"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(research_router, prefix="/research", tags=["research"])
