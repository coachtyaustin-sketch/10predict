"""Generates quantitative predictions from simulation results."""

import structlog

from app.models.chain import EffectChain
from app.models.simulation import SimulationRun
from app.models.prediction import Prediction

logger = structlog.get_logger()

# Signal thresholds
STRONG_BUY_THRESHOLD = 5.0
BUY_THRESHOLD = 2.0
SELL_THRESHOLD = -2.0
STRONG_SELL_THRESHOLD = -5.0
HIGH_CONFIDENCE_THRESHOLD = 0.6


def generate_prediction(
    chain: EffectChain,
    simulation: SimulationRun,
    stock_price: float,
    cycle_type: str,
    why_most_miss_it: str = "",
) -> Prediction:
    """Generate a prediction from chain analysis + simulation results.

    Composite score formula:
        0.40 * weighted_agent_vote    (swarm consensus)
        0.25 * sentiment_score        (overall sentiment direction)
        0.20 * connection_strength    (chain analysis quality)
        0.15 * consensus_strength     (agreement level - high agreement = conviction)
    """
    # Composite score calculation
    raw_score = (
        0.40 * simulation.weighted_vote
        + 0.25 * (simulation.sentiment_score * 10)  # scale -1..1 to -10..10
        + 0.20 * (chain.connection_strength * 10)  # scale 0..1 to 0..10
        + 0.15 * (simulation.consensus_strength * simulation.weighted_vote)
    )

    # Clamp to -10..10
    score = max(-10.0, min(10.0, raw_score))

    # Confidence combines consensus strength and chain connection strength
    confidence = (
        0.5 * simulation.consensus_strength + 0.5 * chain.connection_strength
    )
    confidence = max(0.0, min(1.0, confidence))

    # Determine signal
    if score >= STRONG_BUY_THRESHOLD and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        signal = "STRONG_BUY"
    elif score >= BUY_THRESHOLD:
        signal = "BUY"
    elif score <= STRONG_SELL_THRESHOLD and confidence >= HIGH_CONFIDENCE_THRESHOLD:
        signal = "STRONG_SELL"
    elif score <= SELL_THRESHOLD:
        signal = "SELL"
    else:
        signal = "HOLD"

    # Extract bull/bear cases from agent votes
    bull_case, bear_case, catalysts, risks = _extract_cases(simulation)

    # Estimate price targets based on score magnitude
    move_pct = abs(score) / 10.0 * 0.15  # max 15% move estimate
    if score > 0:
        target_low = stock_price * (1 + move_pct * 0.3)
        target_high = stock_price * (1 + move_pct)
    elif score < 0:
        target_low = stock_price * (1 - move_pct)
        target_high = stock_price * (1 - move_pct * 0.3)
    else:
        target_low = stock_price * 0.95
        target_high = stock_price * 1.05

    prediction = Prediction(
        ticker=chain.ticker,
        chain_id=chain.id,
        cycle_type=cycle_type,
        signal=signal,
        score=round(score, 2),
        confidence=round(confidence, 3),
        chain_depth=chain.chain_depth,
        chain_narrative=chain.chain_narrative,
        why_most_miss_it=why_most_miss_it,
        bull_case=bull_case,
        bear_case=bear_case,
        key_catalysts=catalysts,
        risk_factors=risks,
        price_at_prediction=stock_price,
        target_price_low=round(target_low, 2),
        target_price_high=round(target_high, 2),
        timeframe_days=5,
    )

    logger.info(
        "Prediction generated",
        ticker=chain.ticker,
        signal=signal,
        score=f"{score:.2f}",
        confidence=f"{confidence:.3f}",
        chain=chain.chain_narrative,
    )

    return prediction


def _extract_cases(simulation: SimulationRun) -> tuple[str, str, list, list]:
    """Extract bull/bear cases from agent votes."""
    bull_points = []
    bear_points = []
    catalysts = []
    risks = []

    for key, vote in (simulation.agent_votes or {}).items():
        rating = vote.get("rating", 0)
        reasoning = vote.get("reasoning", "")
        persona = vote.get("persona", "")

        if rating > 2:
            bull_points.append(f"[{vote.get('role', persona)}]: {reasoning[:200]}")
        elif rating < -2:
            bear_points.append(f"[{vote.get('role', persona)}]: {reasoning[:200]}")

        # Extract catalysts from timing analysts
        if persona == "timing_analyst" and rating > 0:
            catalysts.append(reasoning[:200])

        # Extract risks from risk assessors
        if persona == "risk_assessor":
            risks.append(reasoning[:200])

    bull_case = "\n".join(bull_points[:3]) or "No strong bull arguments emerged."
    bear_case = "\n".join(bear_points[:3]) or "No strong bear arguments emerged."

    return bull_case, bear_case, catalysts[:5], risks[:5]
