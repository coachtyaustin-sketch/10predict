"""Generates human-readable prediction reports using LLM."""

import structlog
from openai import AsyncOpenAI

from app.config import settings
from app.models.prediction import Prediction
from app.models.simulation import SimulationRun

logger = structlog.get_logger()

REPORT_PROMPT = """Generate a concise stock prediction report for a penny stock hidden play.

STOCK: {ticker} at ${price:.2f}
SIGNAL: {signal} (Score: {score:.1f}/10, Confidence: {confidence:.0%})

CHAIN OF EFFECTS: {chain_narrative}
CHAIN DEPTH: {chain_depth} orders deep

WHY MOST MISS IT: {why_most_miss_it}

BULL CASE:
{bull_case}

BEAR CASE:
{bear_case}

TARGET RANGE: ${target_low:.2f} - ${target_high:.2f} (next {timeframe} trading days)

SIMULATION RESULTS:
- {agent_count} agents debated this chain
- Weighted consensus: {weighted_vote:.1f}/10
- Sentiment score: {sentiment:.2f}
- Consensus strength: {consensus:.0%}

Write a report in this format:

## {ticker} - {signal}
**Chain:** [one-line chain narrative]
**The Hidden Play:** [2-3 sentences on why most investors miss this]

**Bull Case:** [2-3 bullet points]
**Bear Case:** [2-3 bullet points]
**Key Catalyst:** [what specific event could trigger the move]
**Risk Level:** [low/medium/high + brief reason]
**Timing:** [near-term or longer-term play]

**Bottom Line:** [one decisive sentence]"""


async def generate_report(
    prediction: Prediction,
    simulation: SimulationRun,
) -> str:
    """Generate a human-readable report for a prediction."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model_reports,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a financial analyst writing concise, actionable "
                        "penny stock reports. Be direct, specific, and honest about "
                        "risks. No fluff."
                    ),
                },
                {
                    "role": "user",
                    "content": REPORT_PROMPT.format(
                        ticker=prediction.ticker,
                        price=prediction.price_at_prediction,
                        signal=prediction.signal,
                        score=prediction.score,
                        confidence=prediction.confidence,
                        chain_narrative=prediction.chain_narrative,
                        chain_depth=prediction.chain_depth,
                        why_most_miss_it=prediction.why_most_miss_it,
                        bull_case=prediction.bull_case,
                        bear_case=prediction.bear_case,
                        target_low=prediction.target_price_low or 0,
                        target_high=prediction.target_price_high or 0,
                        timeframe=prediction.timeframe_days,
                        agent_count=simulation.agent_count,
                        weighted_vote=simulation.weighted_vote,
                        sentiment=simulation.sentiment_score,
                        consensus=simulation.consensus_strength,
                    ),
                },
            ],
            temperature=0.4,
            max_tokens=800,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        logger.error("Report generation failed", ticker=prediction.ticker, error=str(e))
        return f"Report generation failed: {str(e)}"
