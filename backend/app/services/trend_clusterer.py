"""Clusters articles into macro trends using LLM analysis.

Instead of matching articles to known stocks, we identify TRENDS first,
then reason about which stocks they affect through chain-of-effects.
"""

import json

import structlog
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.article import Article
from app.models.trend import Trend, TrendArticle

logger = structlog.get_logger()

CLUSTER_PROMPT = """You are a financial trend analyst. Given a batch of recent news articles and Reddit posts, identify the distinct MACRO TRENDS that could move stock prices.

Focus on:
- Industry shifts (new tech, regulation changes, supply chain disruptions)
- Macro events (interest rates, trade policy, government spending)
- Sector momentum (biotech breakthroughs, energy transitions, AI expansion)
- Market catalysts (earnings surprises, M&A activity, FDA decisions)
- Social/retail sentiment surges (meme stocks, Reddit momentum, viral narratives)

IMPORTANT: Look for the UNDERLYING trends, not individual stock mentions.
Example: 5 articles about different AI companies = 1 trend "AI Infrastructure Expansion"

Articles:
{articles_text}

Return a JSON array of trends. Each trend:
{{
    "name": "short descriptive name",
    "summary": "2-3 sentence description of the trend and why it matters",
    "category": "tech|energy|biotech|finance|materials|consumer|industrial|policy|crypto|social",
    "article_indices": [0, 3, 7],  // which articles relate to this trend (0-indexed)
    "momentum": "emerging|building|peak|fading",
    "market_impact": "high|medium|low"
}}

Return ONLY the JSON array, no markdown formatting. Limit to the top 10 most significant trends."""


async def cluster_articles_into_trends(
    articles: list[Article],
    db: AsyncSession,
) -> list[Trend]:
    """Cluster a batch of articles into macro trends using LLM analysis."""
    if not articles:
        return []

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Build article text for the prompt
    articles_text = ""
    for i, article in enumerate(articles):
        body_preview = article.body[:300] if article.body else ""
        articles_text += (
            f"[{i}] ({article.source}) {article.title}\n{body_preview}\n\n"
        )

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model_chain,
            messages=[
                {"role": "system", "content": "You are a financial market trend analyst."},
                {"role": "user", "content": CLUSTER_PROMPT.format(articles_text=articles_text)},
            ],
            temperature=0.3,
            max_tokens=3000,
        )

        content = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]

        trend_data = json.loads(content)

    except Exception as e:
        logger.error("Trend clustering failed", error=str(e))
        return []

    # Store trends in database
    trends = []
    for td in trend_data:
        trend = Trend(
            name=td["name"],
            summary=td["summary"],
            category=td.get("category", "other"),
            article_count=len(td.get("article_indices", [])),
        )
        db.add(trend)
        await db.flush()  # get the ID

        # Link articles to trend
        for idx in td.get("article_indices", []):
            if 0 <= idx < len(articles):
                link = TrendArticle(
                    trend_id=trend.id,
                    article_id=articles[idx].id,
                    relevance=1.0 if td.get("market_impact") == "high" else 0.7,
                )
                db.add(link)

        trends.append(trend)

    await db.commit()
    logger.info("Clustered articles into trends", trend_count=len(trends))
    return trends
