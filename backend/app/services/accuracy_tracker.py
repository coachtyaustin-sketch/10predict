"""Tracks prediction accuracy by comparing predictions to actual price movements."""

import datetime

import structlog
import yfinance as yf
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.models.accuracy import PredictionAccuracy

logger = structlog.get_logger()


async def evaluate_past_predictions(db: AsyncSession):
    """Check predictions from 1-5 days ago and record accuracy.

    Runs as part of each research cycle to close the feedback loop.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    cutoff_start = now - datetime.timedelta(days=6)
    cutoff_end = now - datetime.timedelta(days=1)

    # Find predictions that need evaluation
    result = await db.execute(
        select(Prediction).where(
            and_(
                Prediction.created_at >= cutoff_start,
                Prediction.created_at <= cutoff_end,
                ~Prediction.id.in_(
                    select(PredictionAccuracy.prediction_id)
                    .where(PredictionAccuracy.actual_price_1d.isnot(None))
                ),
            )
        )
    )
    predictions = result.scalars().all()

    if not predictions:
        logger.info("No predictions to evaluate")
        return

    # Group by ticker to batch yfinance calls
    tickers = list(set(p.ticker for p in predictions))
    price_data = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="10d")
            if not hist.empty:
                price_data[ticker] = hist
        except Exception as e:
            logger.warning("Failed to fetch price history", ticker=ticker, error=str(e))

    for prediction in predictions:
        if prediction.ticker not in price_data:
            continue

        hist = price_data[prediction.ticker]
        pred_date = prediction.created_at.date()

        # Find actual prices at 1d, 3d, 5d after prediction
        actual_1d = _get_price_at_offset(hist, pred_date, 1)
        actual_3d = _get_price_at_offset(hist, pred_date, 3)
        actual_5d = _get_price_at_offset(hist, pred_date, 5)

        pred_price = prediction.price_at_prediction
        is_bullish = prediction.signal in ("STRONG_BUY", "BUY")

        pct_1d = ((actual_1d - pred_price) / pred_price * 100) if actual_1d else None
        pct_3d = ((actual_3d - pred_price) / pred_price * 100) if actual_3d else None
        pct_5d = ((actual_5d - pred_price) / pred_price * 100) if actual_5d else None

        # Check if direction was correct
        dir_1d = (pct_1d > 0) == is_bullish if pct_1d is not None else None
        dir_3d = (pct_3d > 0) == is_bullish if pct_3d is not None else None
        dir_5d = (pct_5d > 0) == is_bullish if pct_5d is not None else None

        # Check for significant move (>5% in predicted direction)
        max_move = max(abs(pct_1d or 0), abs(pct_3d or 0), abs(pct_5d or 0))
        significant = max_move >= 5.0 and (
            (is_bullish and max_move == max(pct_1d or 0, pct_3d or 0, pct_5d or 0))
            or (not is_bullish and max_move == max(abs(pct_1d or 0), abs(pct_3d or 0), abs(pct_5d or 0)))
        )

        accuracy = PredictionAccuracy(
            prediction_id=prediction.id,
            ticker=prediction.ticker,
            prediction_price=pred_price,
            predicted_signal=prediction.signal,
            actual_price_1d=actual_1d,
            actual_price_3d=actual_3d,
            actual_price_5d=actual_5d,
            pct_change_1d=round(pct_1d, 2) if pct_1d is not None else None,
            pct_change_3d=round(pct_3d, 2) if pct_3d is not None else None,
            pct_change_5d=round(pct_5d, 2) if pct_5d is not None else None,
            direction_correct_1d=dir_1d,
            direction_correct_3d=dir_3d,
            direction_correct_5d=dir_5d,
            significant_move_achieved=significant,
            max_move_pct=round(max_move, 2),
            evaluated_at=now,
        )
        db.add(accuracy)

        logger.info(
            "Evaluated prediction",
            ticker=prediction.ticker,
            signal=prediction.signal,
            pct_1d=pct_1d,
            pct_5d=pct_5d,
            correct_5d=dir_5d,
            significant=significant,
        )

    await db.commit()
    logger.info("Accuracy evaluation complete", evaluated=len(predictions))


def _get_price_at_offset(hist, pred_date, days_offset: int) -> float | None:
    """Get closing price N trading days after prediction date."""
    target_date = pred_date + datetime.timedelta(days=days_offset)
    # Find nearest trading day
    for offset in range(3):  # look up to 3 days forward for weekends
        check_date = target_date + datetime.timedelta(days=offset)
        matching = hist.index[hist.index.date == check_date]
        if len(matching) > 0:
            return float(hist.loc[matching[0], "Close"])
    return None
