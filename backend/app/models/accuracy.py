import datetime
from sqlalchemy import String, Float, Boolean, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class PredictionAccuracy(Base):
    """Tracks how predictions performed against actual price movements."""

    __tablename__ = "prediction_accuracy"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int] = mapped_column(ForeignKey("predictions.id"), unique=True)
    ticker: Mapped[str] = mapped_column(String(10), index=True)

    prediction_price: Mapped[float] = mapped_column(Float)
    predicted_signal: Mapped[str] = mapped_column(String(20))

    actual_price_1d: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_price_3d: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_price_5d: Mapped[float | None] = mapped_column(Float, nullable=True)

    pct_change_1d: Mapped[float | None] = mapped_column(Float, nullable=True)
    pct_change_3d: Mapped[float | None] = mapped_column(Float, nullable=True)
    pct_change_5d: Mapped[float | None] = mapped_column(Float, nullable=True)

    direction_correct_1d: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    direction_correct_3d: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    direction_correct_5d: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Did it make a "significant move" (>5%) in the predicted direction?
    significant_move_achieved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    max_move_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    days_to_max_move: Mapped[int | None] = mapped_column(Integer, nullable=True)

    evaluated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
