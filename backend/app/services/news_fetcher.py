"""Fetches financial news from Finnhub and RSS feeds."""

import datetime
from hashlib import md5

import feedparser
import finnhub
import structlog

from app.config import settings

logger = structlog.get_logger()

RSS_FEEDS = [
    ("https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC&region=US&lang=en-US", "yahoo"),
    ("https://www.investing.com/rss/news.rss", "investing_com"),
    ("https://feeds.marketwatch.com/marketwatch/topstories/", "marketwatch"),
    ("https://seekingalpha.com/market_currents.xml", "seekingalpha"),
]


def fetch_finnhub_news(category: str = "general") -> list[dict]:
    """Fetch general market news from Finnhub."""
    if not settings.finnhub_api_key:
        logger.warning("Finnhub API key not configured, skipping")
        return []

    client = finnhub.Client(api_key=settings.finnhub_api_key)
    articles = []

    try:
        news = client.general_news(category, min_id=0)
        for item in news[:50]:  # limit to 50 per call
            articles.append({
                "source": "finnhub",
                "source_id": f"finnhub_{item.get('id', md5(item['headline'].encode()).hexdigest())}",
                "title": item.get("headline", ""),
                "body": item.get("summary", ""),
                "url": item.get("url", ""),
                "author": item.get("source", ""),
                "subreddit": None,
                "score": 0.0,
                "published_at": datetime.datetime.fromtimestamp(
                    item.get("datetime", 0), tz=datetime.timezone.utc
                ),
            })
        logger.info("Fetched Finnhub news", count=len(articles))
    except Exception as e:
        logger.error("Finnhub fetch failed", error=str(e))

    return articles


def fetch_rss_feeds() -> list[dict]:
    """Fetch articles from financial RSS feeds."""
    articles = []

    for feed_url, source_name in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:20]:
                # Parse published date
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime.datetime(*entry.published_parsed[:6],
                                                   tzinfo=datetime.timezone.utc)
                if not published:
                    published = datetime.datetime.now(datetime.timezone.utc)

                source_id = f"rss_{source_name}_{md5(entry.get('link', entry.get('title', '')).encode()).hexdigest()}"

                articles.append({
                    "source": "rss",
                    "source_id": source_id,
                    "title": entry.get("title", ""),
                    "body": entry.get("summary", entry.get("description", ""))[:3000],
                    "url": entry.get("link", ""),
                    "author": source_name,
                    "subreddit": None,
                    "score": 0.0,
                    "published_at": published,
                })

            logger.info("Fetched RSS feed", source=source_name, count=len(feed.entries))

        except Exception as e:
            logger.error("RSS fetch failed", source=source_name, error=str(e))
            continue

    return articles
