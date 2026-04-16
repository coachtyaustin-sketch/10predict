"""The Chain-of-Effects Analyzer - the core brain of 10Predict.

For each trend, reasons through N-order effects to discover penny stocks
that most investors miss. This is the key differentiator.

Example chain: AI Data Center Boom -> Power Demand Surge -> Small Energy Producers -> $USEG
"""

import json

import structlog
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.trend import Trend
from app.models.chain import EffectChain, ChainLink
from app.services.ticker_validator import validate_and_cache_ticker

logger = structlog.get_logger()

CHAIN_ANALYSIS_PROMPT = """You are an elite supply chain and market effects analyst. Your specialty is finding HIDDEN PLAYS - the 2nd and 3rd order effects that most investors completely miss.

Given this market trend, reason through the FULL dependency chain to find penny stocks (under $10) that could make significant moves.

TREND: {trend_name}
DETAILS: {trend_summary}

Think through these dimensions AT LEAST 3 levels deep:
1. REQUIRES - What does this trend need? (inputs, resources, infrastructure, raw materials)
2. ENABLES - What new markets or businesses does this create downstream?
3. DISPLACES - What industries/companies lose? (short opportunities)
4. REGULATES - Who benefits from regulating or servicing this trend?
5. SUPPORTS - What logistics, services, or real estate benefits?

For each chain, think like this:
- Level 1 (obvious): "AI boom helps NVIDIA" - SKIP, everyone knows this
- Level 2 (less obvious): "AI needs massive power" - getting warmer
- Level 3 (hidden play): "Small utility companies near data center sites" - THIS IS WHAT WE WANT

IMPORTANT RULES:
- Focus on stocks that trade on NYSE, NASDAQ, or AMEX (Robinhood-tradeable)
- Target stocks under $10 - these are penny stocks
- The more indirect and non-obvious the connection, the MORE valuable
- Each chain must have a LOGICAL, defensible reasoning path
- Include both bullish AND bearish chains (who loses from this trend?)

Return a JSON array of chain discoveries:
{{
    "ticker": "USEG",
    "company_name": "US Energy Corp",
    "chain_narrative": "AI Data Centers -> Massive Power Demand -> Small Energy Producers",
    "chain_links": [
        {{
            "from": "AI Data Center Expansion",
            "to": "Semiconductor Manufacturing",
            "relationship": "REQUIRES",
            "explanation": "AI models need custom chips, driving fab expansion"
        }},
        {{
            "from": "Semiconductor Manufacturing",
            "to": "Power Grid Infrastructure",
            "relationship": "REQUIRES",
            "explanation": "Both data centers and chip fabs consume enormous electricity"
        }},
        {{
            "from": "Power Grid Infrastructure",
            "to": "US Energy Corp (USEG)",
            "relationship": "ENABLES",
            "explanation": "Small energy producers near planned data center sites benefit from increased local power demand"
        }}
    ],
    "chain_depth": 3,
    "connection_strength": 0.65,
    "direction": "bullish",
    "reasoning": "USEG operates energy assets in regions where multiple data centers are planned. As power demand outstrips local supply, small producers see pricing power increase.",
    "why_most_miss_it": "Investors focus on NVDA and cloud stocks. They miss that the power bottleneck benefits small, overlooked energy companies in the right locations."
}}

Return 3-8 chain discoveries per trend. Focus on QUALITY over quantity.
Return ONLY the JSON array, no markdown."""


async def analyze_chain_effects(
    trend: Trend,
    db: AsyncSession,
) -> list[EffectChain]:
    """Analyze a trend for N-order effect chains leading to penny stock opportunities."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model_chain,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert at finding hidden market plays through "
                        "supply chain and dependency analysis. You think 3+ levels "
                        "deep where most analysts stop at level 1."
                    ),
                },
                {
                    "role": "user",
                    "content": CHAIN_ANALYSIS_PROMPT.format(
                        trend_name=trend.name,
                        trend_summary=trend.summary,
                    ),
                },
            ],
            temperature=0.5,
            max_tokens=4000,
        )

        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            if content.endswith("```"):
                content = content[:-3]

        chain_data = json.loads(content)

    except Exception as e:
        logger.error("Chain analysis failed", trend=trend.name, error=str(e))
        return []

    # Validate each discovered ticker and store valid chains
    valid_chains = []
    for cd in chain_data:
        ticker = cd.get("ticker", "").upper().strip()
        if not ticker:
            continue

        # Validate: is it under $10, Robinhood-tradeable?
        validation = await validate_and_cache_ticker(ticker, db)
        if not validation.is_valid:
            logger.info(
                "Chain ticker rejected",
                ticker=ticker,
                reason=validation.reason,
                trend=trend.name,
            )
            continue

        # Store the chain
        chain = EffectChain(
            trend_id=trend.id,
            ticker=ticker,
            company_name=cd.get("company_name", validation.name),
            chain_depth=cd.get("chain_depth", len(cd.get("chain_links", []))),
            chain_narrative=cd.get("chain_narrative", ""),
            chain_links=cd.get("chain_links", []),
            connection_strength=cd.get("connection_strength", 0.5),
            direction=cd.get("direction", "bullish"),
            reasoning=cd.get("reasoning", ""),
        )
        db.add(chain)
        await db.flush()

        # Store individual chain links
        for i, link_data in enumerate(cd.get("chain_links", [])):
            link = ChainLink(
                chain_id=chain.id,
                order=i + 1,
                from_entity=link_data.get("from", ""),
                to_entity=link_data.get("to", ""),
                relationship_type=link_data.get("relationship", "REQUIRES"),
                strength=cd.get("connection_strength", 0.5),
                explanation=link_data.get("explanation", ""),
            )
            db.add(link)

        valid_chains.append(chain)
        logger.info(
            "Chain discovered",
            ticker=ticker,
            price=validation.price,
            chain=cd.get("chain_narrative"),
            depth=chain.chain_depth,
            strength=chain.connection_strength,
        )

    await db.commit()
    logger.info(
        "Chain analysis complete",
        trend=trend.name,
        total_chains=len(chain_data),
        valid_chains=len(valid_chains),
    )
    return valid_chains
