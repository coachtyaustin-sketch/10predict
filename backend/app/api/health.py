from fastapi import APIRouter

from app.scheduler.scheduler import get_scheduler_status

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "0.1.0",
        "scheduler": get_scheduler_status(),
    }
