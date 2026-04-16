from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionResponse, PredictionSummary

router = APIRouter()


@router.get("", response_model=list[PredictionSummary])
async def list_predictions(
    signal: str | None = None,
    ticker: str | None = None,
    min_confidence: float | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List predictions with optional filters."""
    query = select(Prediction).order_by(desc(Prediction.created_at))

    if signal:
        query = query.where(Prediction.signal == signal.upper())
    if ticker:
        query = query.where(Prediction.ticker == ticker.upper())
    if min_confidence is not None:
        query = query.where(Prediction.confidence >= min_confidence)

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/latest", response_model=list[PredictionSummary])
async def latest_predictions(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent predictions."""
    result = await db.execute(
        select(Prediction).order_by(desc(Prediction.created_at)).limit(limit)
    )
    return result.scalars().all()


@router.get("/{prediction_id}", response_model=PredictionResponse)
async def get_prediction(
    prediction_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get full prediction details including report."""
    result = await db.execute(
        select(Prediction).where(Prediction.id == prediction_id)
    )
    prediction = result.scalar_one_or_none()
    if not prediction:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Prediction not found")
    return prediction
