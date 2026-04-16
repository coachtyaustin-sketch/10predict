import datetime
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base


class Trend(Base):
    """A clustered macro trend extracted from articles (e.g., 'AI Data Center Expansion')."""

    __tablename__ = "trends"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(500))
    summary: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100))  # tech, energy, biotech, etc.
    article_count: Mapped[int] = mapped_column(Integer, default=1)
    first_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    articles: Mapped[list["TrendArticle"]] = relationship(back_populates="trend")
    chains: Mapped[list["EffectChain"]] = relationship(  # noqa: F821
        "EffectChain", back_populates="trend"
    )


class TrendArticle(Base):
    """Links articles to trends."""

    __tablename__ = "trend_articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    trend_id: Mapped[int] = mapped_column(ForeignKey("trends.id"))
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id"))
    relevance: Mapped[float] = mapped_column(default=1.0)

    trend: Mapped["Trend"] = relationship(back_populates="articles")
