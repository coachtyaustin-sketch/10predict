from fastapi import APIRouter, Depends
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.prediction import Prediction
from app.models.accuracy import PredictionAccuracy
from app.schemas.dashboard import DashboardSummary, AccuracyMetrics
from app.schemas.prediction import SignalResponse
from app.scheduler.scheduler import get_scheduler_status

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def dashboard_summary(db: AsyncSession = Depends(get_db)):
    """Get dashboard summary with key metrics."""
    # Total predictions
    total = await db.execute(select(func.count(Prediction.id)))
    total_predictions = total.scalar() or 0

    # Active signals (non-HOLD)
    active = await db.execute(
        select(func.count(Prediction.id)).where(Prediction.signal != "HOLD")
    )
    active_signals = active.scalar() or 0

    # Accuracy rate (5-day direction correct)
    acc_result = await db.execute(
        select(
            func.count(PredictionAccuracy.id),
            func.avg(
                func.cast(PredictionAccuracy.direction_correct_5d, func.text())
                .cast(func.integer())
            ),
        ).where(PredictionAccuracy.direction_correct_5d.isnot(None))
    )
    acc_row = acc_result.one()
    accuracy_count = acc_row[0] or 0
    accuracy_rate = float(acc_row[1] * 100) if acc_row[1] is not None else None

    # Top signals by confidence
    top_result = await db.execute(
        select(Prediction)
        .where(Prediction.signal != "HOLD")
        .order_by(desc(Prediction.confidence))
        .limit(5)
    )
    top_signals = top_result.scalars().all()

    # Recent predictions
    recent_result = await db.execute(
        select(Prediction).order_by(desc(Prediction.created_at)).limit(10)
    )
    recent = recent_result.scalars().all()

    return DashboardSummary(
        total_predictions=total_predictions,
        active_signals=active_signals,
        accuracy_rate=accuracy_rate,
        accuracy_count=accuracy_count,
        top_signals=[SignalResponse.model_validate(s) for s in top_signals],
        recent_predictions=[SignalResponse.model_validate(p) for p in recent],
        scheduler_status=get_scheduler_status(),
    )


@router.get("/accuracy", response_model=AccuracyMetrics)
async def accuracy_metrics(db: AsyncSession = Depends(get_db)):
    """Get overall prediction accuracy metrics."""
    result = await db.execute(
        select(
            func.count(PredictionAccuracy.id),
            func.avg(
                func.case(
                    (PredictionAccuracy.direction_correct_1d.is_(True), 1.0),
                    else_=0.0,
                )
            ),
            func.avg(
                func.case(
                    (PredictionAccuracy.direction_correct_3d.is_(True), 1.0),
                    else_=0.0,
                )
            ),
            func.avg(
                func.case(
                    (PredictionAccuracy.direction_correct_5d.is_(True), 1.0),
                    else_=0.0,
                )
            ),
            func.avg(
                func.case(
                    (PredictionAccuracy.significant_move_achieved.is_(True), 1.0),
                    else_=0.0,
                )
            ),
            func.avg(PredictionAccuracy.max_move_pct),
        ).where(PredictionAccuracy.evaluated_at.isnot(None))
    )
    row = result.one()

    return AccuracyMetrics(
        total_evaluated=row[0] or 0,
        direction_correct_1d=round(row[1] * 100, 1) if row[1] is not None else None,
        direction_correct_3d=round(row[2] * 100, 1) if row[2] is not None else None,
        direction_correct_5d=round(row[3] * 100, 1) if row[3] is not None else None,
        significant_moves_hit=round(row[4] * 100, 1) if row[4] is not None else None,
        avg_max_move_pct=round(row[5], 2) if row[5] is not None else None,
    )
