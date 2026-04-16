import datetime
from sqlalchemy import String, Text, DateTime, Float, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class EffectChain(Base):
    """An N-order effect chain from a trend to a target stock.

    Example: AI Boom -> Power Demand -> Small Energy Producers -> $USEG
    """

    __tablename__ = "effect_chains"

    id: Mapped[int] = mapped_column(primary_key=True)
    trend_id: Mapped[int] = mapped_column(ForeignKey("trends.id"))
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    company_name: Mapped[str] = mapped_column(String(500))
    chain_depth: Mapped[int] = mapped_column(Integer)  # 1=direct, 2=second-order, etc.
    chain_narrative: Mapped[str] = mapped_column(Text)  # "AI -> Chips -> Power -> USEG"
    chain_links: Mapped[dict] = mapped_column(JSONB, default=list)  # structured chain steps
    connection_strength: Mapped[float] = mapped_column(Float)  # 0.0 to 1.0
    direction: Mapped[str] = mapped_column(String(10))  # bullish, bearish
    reasoning: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    trend: Mapped["Trend"] = relationship(back_populates="chains")  # noqa: F821
    links: Mapped[list["ChainLink"]] = relationship(back_populates="chain")


class ChainLink(Base):
    """Individual step in an effect chain."""

    __tablename__ = "chain_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("effect_chains.id"))
    order: Mapped[int] = mapped_column(Integer)  # 1, 2, 3...
    from_entity: Mapped[str] = mapped_column(String(500))  # "AI Data Centers"
    to_entity: Mapped[str] = mapped_column(String(500))  # "Power Generation"
    relationship_type: Mapped[str] = mapped_column(String(100))  # REQUIRES, ENABLES, DISPLACES
    strength: Mapped[float] = mapped_column(Float)
    explanation: Mapped[str] = mapped_column(Text)

    chain: Mapped["EffectChain"] = relationship(back_populates="links")
