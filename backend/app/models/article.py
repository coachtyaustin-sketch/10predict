import datetime
from sqlalchemy import String, Text, DateTime, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Article(Base):
    """A news article, Reddit post, blog entry, or SEC filing."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(50))  # reddit, finnhub, rss, sec
    source_id: Mapped[str] = mapped_column(String(255), unique=True)
    title: Mapped[str] = mapped_column(Text)
    body: Mapped[str] = mapped_column(Text, default="")
    url: Mapped[str] = mapped_column(Text, default="")
    author: Mapped[str] = mapped_column(String(255), default="")
    subreddit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)  # upvotes, relevance
    published_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    fetched_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
