from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.prediction import Prediction
from app.schemas.prediction import SignalResponse

router = APIRouter()


@router.get("", response_model=list[SignalResponse])
async def active_signals(
    signal_type: str | None = None,
    min_score: float | None = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get current active signals sorted by confidence.

    Active signals are the most recent prediction per ticker
    where signal is not HOLD.
    """
    # Subquery: latest prediction per ticker
    subq = (
        select(
            Prediction.ticker,
            func.max(Prediction.id).label("max_id"),
        )
        .group_by(Prediction.ticker)
        .subquery()
    )

    query = (
        select(Prediction)
        .join(subq, Prediction.id == subq.c.max_id)
        .where(Prediction.signal != "HOLD")
    )

    if signal_type:
        query = query.where(Prediction.signal == signal_type.upper())
    if min_score is not None:
        query = query.where(Prediction.score >= min_score)

    query = query.order_by(desc(Prediction.confidence)).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
