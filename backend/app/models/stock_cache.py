import datetime
from sqlalchemy import String, Float, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class StockCache(Base):
    """Lightweight cache of stocks discovered through research.

    Not a managed universe - just a cache of tickers we've seen and validated.
    """

    __tablename__ = "stock_cache"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(500))
    exchange: Mapped[str] = mapped_column(String(20))  # NYSE, NASDAQ, AMEX
    sector: Mapped[str] = mapped_column(String(200), default="")
    industry: Mapped[str] = mapped_column(String(200), default="")
    last_price: Mapped[float] = mapped_column(Float, nullable=True)
    market_cap: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_robinhood_eligible: Mapped[bool] = mapped_column(Boolean, default=False)
    last_validated_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
