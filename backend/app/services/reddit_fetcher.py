"""Fetches posts from penny-stock-focused subreddits via PRAW."""

import datetime

import praw
import structlog

from app.config import settings

logger = structlog.get_logger()

TARGET_SUBREDDITS = [
    "pennystocks",
    "wallstreetbets",
    "stocks",
    "RobinHoodPennyStocks",
    "smallstreetbets",
    "investing",
    "StockMarket",
]


def _build_reddit_client() -> praw.Reddit | None:
    if not settings.reddit_client_id or not settings.reddit_client_secret:
        logger.warning("Reddit credentials not configured, skipping")
        return None
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent,
    )


def fetch_reddit_posts(
    subreddits: list[str] | None = None,
    limit_per_sub: int = 25,
    time_filter: str = "day",
) -> list[dict]:
    """Fetch hot/new posts from target subreddits.

    Returns list of normalized article dicts.
    """
    client = _build_reddit_client()
    if not client:
        return []

    subs = subreddits or TARGET_SUBREDDITS
    articles = []

    for sub_name in subs:
        try:
            subreddit = client.subreddit(sub_name)
            for post in subreddit.hot(limit=limit_per_sub):
                # Skip stickied mod posts
                if post.stickied:
                    continue

                articles.append({
                    "source": "reddit",
                    "source_id": f"reddit_{post.id}",
                    "title": post.title,
                    "body": post.selftext[:5000] if post.selftext else "",
                    "url": f"https://reddit.com{post.permalink}",
                    "author": str(post.author) if post.author else "[deleted]",
                    "subreddit": sub_name,
                    "score": float(post.score),
                    "published_at": datetime.datetime.fromtimestamp(
                        post.created_utc, tz=datetime.timezone.utc
                    ),
                    "comment_count": post.num_comments,
                })

            # Also grab top posts for broader coverage
            for post in subreddit.top(time_filter=time_filter, limit=limit_per_sub // 2):
                if post.stickied:
                    continue
                source_id = f"reddit_{post.id}"
                if any(a["source_id"] == source_id for a in articles):
                    continue
                articles.append({
                    "source": "reddit",
                    "source_id": source_id,
                    "title": post.title,
                    "body": post.selftext[:5000] if post.selftext else "",
                    "url": f"https://reddit.com{post.permalink}",
                    "author": str(post.author) if post.author else "[deleted]",
                    "subreddit": sub_name,
                    "score": float(post.score),
                    "published_at": datetime.datetime.fromtimestamp(
                        post.created_utc, tz=datetime.timezone.utc
                    ),
                    "comment_count": post.num_comments,
                })

            logger.info("Fetched Reddit posts", subreddit=sub_name, count=len(articles))

        except Exception as e:
            logger.error("Reddit fetch failed", subreddit=sub_name, error=str(e))
            continue

    return articles
