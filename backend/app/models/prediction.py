import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Prediction(Base):
    """A prediction for a stock based on chain-of-effects analysis + swarm simulation."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("effect_chains.id"))
    cycle_type: Mapped[str] = mapped_column(String(20))  # pre_market, midday, after_hours

    # Signal
    signal: Mapped[str] = mapped_column(String(20))  # STRONG_BUY, BUY, HOLD, SELL, STRONG_SELL
    score: Mapped[float] = mapped_column(Float)  # -10.0 to 10.0
    confidence: Mapped[float] = mapped_column(Float)  # 0.0 to 1.0

    # Chain context
    chain_depth: Mapped[int] = mapped_column(Integer)
    chain_narrative: Mapped[str] = mapped_column(Text)
    why_most_miss_it: Mapped[str] = mapped_column(Text)  # the hidden play explanation

    # Analysis
    bull_case: Mapped[str] = mapped_column(Text)
    bear_case: Mapped[str] = mapped_column(Text)
    key_catalysts: Mapped[dict] = mapped_column(JSONB, default=list)
    risk_factors: Mapped[dict] = mapped_column(JSONB, default=list)

    # Price at prediction time
    price_at_prediction: Mapped[float] = mapped_column(Float)
    target_price_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_price_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    timeframe_days: Mapped[int] = mapped_column(Integer, default=5)

    # Report
    report_text: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
