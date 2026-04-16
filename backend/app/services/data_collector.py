"""Orchestrates data collection from all sources and stores articles in the database."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.article import Article
from app.services.reddit_fetcher import fetch_reddit_posts
from app.services.news_fetcher import fetch_finnhub_news, fetch_rss_feeds

logger = structlog.get_logger()


async def collect_all_articles(db: AsyncSession) -> list[Article]:
    """Fetch from all sources, deduplicate, and store new articles.

    Returns the list of newly stored articles.
    """
    # Fetch from all sources
    raw_articles = []
    raw_articles.extend(fetch_reddit_posts())
    raw_articles.extend(fetch_finnhub_news())
    raw_articles.extend(fetch_rss_feeds())

    logger.info("Collected raw articles", total=len(raw_articles))

    # Deduplicate against existing articles
    source_ids = [a["source_id"] for a in raw_articles]
    result = await db.execute(
        select(Article.source_id).where(Article.source_id.in_(source_ids))
    )
    existing_ids = set(result.scalars().all())

    new_articles = []
    for raw in raw_articles:
        if raw["source_id"] in existing_ids:
            continue

        article = Article(
            source=raw["source"],
            source_id=raw["source_id"],
            title=raw["title"],
            body=raw["body"],
            url=raw["url"],
            author=raw["author"],
            subreddit=raw.get("subreddit"),
            score=raw.get("score", 0.0),
            published_at=raw["published_at"],
        )
        db.add(article)
        new_articles.append(article)

    if new_articles:
        await db.commit()

    logger.info(
        "Stored new articles",
        new=len(new_articles),
        duplicates=len(raw_articles) - len(new_articles),
    )
    return new_articles
