"""Swarm simulation engine using LLM-based multi-agent debate.

Agents with different personas debate whether a chain-of-effects
connection between a trend and a penny stock is valid and actionable.
This is adapted from MiroFish's OASIS-based simulation but uses
direct LLM calls for cost efficiency.
"""

import json
import time
from statistics import mean, stdev

import structlog
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.agents.persona_types import PersonaType, get_personas_for_simulation
from app.models.chain import EffectChain
from app.models.simulation import SimulationRun, AgentVote

logger = structlog.get_logger()

SEED_POST_TEMPLATE = """STOCK UNDER ANALYSIS: {ticker} ({company_name}) - ${price:.2f}

TREND: {trend_name}
{trend_summary}

CHAIN OF EFFECTS:
{chain_narrative}

DETAILED CHAIN LINKS:
{chain_links_text}

CONNECTION STRENGTH (analyst estimate): {connection_strength:.0%}
DIRECTION: {direction}

REASONING: {reasoning}

QUESTION FOR DEBATE: Is this chain-of-effects connection REAL and ACTIONABLE?
Will {ticker} make a significant move (>5%) in the next 1-5 trading days because of this trend?

Rate your position from -10 (STRONG SELL / chain is bogus) to +10 (STRONG BUY / hidden gem).
"""

DEBATE_PROMPT = """You are participating in a stock analysis debate as a {role}.

{system_prompt}

Here is the stock and chain being debated:
{seed_post}

Previous discussion:
{discussion_history}

Based on your expertise and the discussion so far, provide your analysis.
Then give your final rating from -10 to +10.

Format your response as:
ANALYSIS: [your analysis in 2-4 sentences]
RATING: [number from -10 to +10]
CONFIDENCE: [0.0 to 1.0]"""

FINAL_VOTE_PROMPT = """You are a {role} in a stock analysis debate.

{system_prompt}

STOCK: {ticker} ({company_name}) at ${price:.2f}
CHAIN: {chain_narrative}

Full debate transcript:
{full_transcript}

After hearing all perspectives, give your FINAL position.

FINAL_ANALYSIS: [2-3 sentences, your concluding view]
FINAL_RATING: [number from -10 to +10, where -10=strong sell, 0=neutral, +10=strong buy]
CONFIDENCE: [0.0 to 1.0, how confident you are in this rating]"""


async def run_swarm_simulation(
    chain: EffectChain,
    trend_name: str,
    trend_summary: str,
    stock_price: float,
    db: AsyncSession,
) -> SimulationRun:
    """Run a multi-agent debate simulation for a chain-of-effects discovery."""
    start_time = time.time()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Build seed post
    chain_links_text = ""
    for link in (chain.chain_links or []):
        chain_links_text += (
            f"  {link.get('from')} --[{link.get('relationship')}]--> "
            f"{link.get('to')}: {link.get('explanation')}\n"
        )

    seed_post = SEED_POST_TEMPLATE.format(
        ticker=chain.ticker,
        company_name=chain.company_name,
        price=stock_price,
        trend_name=trend_name,
        trend_summary=trend_summary,
        chain_narrative=chain.chain_narrative,
        chain_links_text=chain_links_text,
        connection_strength=chain.connection_strength,
        direction=chain.direction,
        reasoning=chain.reasoning,
    )

    # Get agent personas
    personas = get_personas_for_simulation(settings.max_agents_per_simulation)
    logger.info(
        "Starting swarm simulation",
        ticker=chain.ticker,
        agents=len(personas),
        rounds=settings.simulation_rounds,
    )

    # Run debate rounds
    transcript = []
    discussion_history = ""

    for round_num in range(settings.simulation_rounds):
        round_posts = []
        for i, persona in enumerate(personas):
            try:
                response = await client.chat.completions.create(
                    model=settings.openai_model_agents,
                    messages=[
                        {"role": "system", "content": persona.system_prompt},
                        {
                            "role": "user",
                            "content": DEBATE_PROMPT.format(
                                role=persona.role,
                                system_prompt=persona.system_prompt,
                                seed_post=seed_post,
                                discussion_history=discussion_history[-3000:],
                            ),
                        },
                    ],
                    temperature=0.7,
                    max_tokens=300,
                )
                post_content = response.choices[0].message.content.strip()
                round_posts.append({
                    "agent": persona.role,
                    "persona": persona.name,
                    "round": round_num + 1,
                    "content": post_content,
                })
                discussion_history += f"\n[{persona.role}]: {post_content}\n"
            except Exception as e:
                logger.warning(
                    "Agent post failed",
                    persona=persona.name,
                    round=round_num,
                    error=str(e),
                )

        transcript.extend(round_posts)

    # Final votes
    agent_votes_data = {}
    vote_records = []
    for i, persona in enumerate(personas):
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model_agents,
                messages=[
                    {"role": "system", "content": persona.system_prompt},
                    {
                        "role": "user",
                        "content": FINAL_VOTE_PROMPT.format(
                            role=persona.role,
                            system_prompt=persona.system_prompt,
                            ticker=chain.ticker,
                            company_name=chain.company_name,
                            price=stock_price,
                            chain_narrative=chain.chain_narrative,
                            full_transcript=discussion_history[-4000:],
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=200,
            )

            vote_text = response.choices[0].message.content.strip()
            rating = _extract_rating(vote_text)
            confidence = _extract_confidence(vote_text)

            agent_votes_data[f"{persona.name}_{i}"] = {
                "persona": persona.name,
                "role": persona.role,
                "rating": rating,
                "confidence": confidence,
                "weight": persona.weight,
                "reasoning": vote_text,
            }

            vote_records.append({
                "persona": persona.name,
                "role": persona.role,
                "rating": rating,
                "confidence": confidence,
                "weight": persona.weight,
                "reasoning": vote_text,
            })

        except Exception as e:
            logger.warning("Final vote failed", persona=persona.name, error=str(e))

    # Calculate aggregate scores
    if vote_records:
        ratings = [v["rating"] for v in vote_records]
        weights = [v["weight"] for v in vote_records]
        weighted_sum = sum(r * w for r, w in zip(ratings, weights))
        total_weight = sum(weights)
        weighted_vote = weighted_sum / total_weight if total_weight > 0 else 0
        sentiment = mean(ratings) / 10.0  # normalize to -1 to 1
        consensus = 1.0 - (stdev(ratings) / 10.0) if len(ratings) > 1 else 0.5
    else:
        weighted_vote = 0
        sentiment = 0
        consensus = 0

    duration = time.time() - start_time

    # Store simulation run
    sim_run = SimulationRun(
        ticker=chain.ticker,
        chain_id=chain.id,
        agent_count=len(personas),
        round_count=settings.simulation_rounds,
        duration_seconds=duration,
        seed_post=seed_post,
        transcript=transcript,
        agent_votes=agent_votes_data,
        weighted_vote=weighted_vote,
        sentiment_score=sentiment,
        consensus_strength=max(0, min(1, consensus)),
    )
    db.add(sim_run)
    await db.flush()

    # Store individual votes
    for vr in vote_records:
        vote = AgentVote(
            simulation_id=sim_run.id,
            agent_persona=vr["persona"],
            agent_name=vr["role"],
            initial_position=vr["rating"],  # simplified: same as final for now
            final_position=vr["rating"],
            confidence=vr["confidence"],
            reasoning=vr["reasoning"],
            weight=vr["weight"],
        )
        db.add(vote)

    await db.commit()

    logger.info(
        "Simulation complete",
        ticker=chain.ticker,
        weighted_vote=f"{weighted_vote:.2f}",
        sentiment=f"{sentiment:.2f}",
        consensus=f"{consensus:.2f}",
        duration=f"{duration:.1f}s",
        agents=len(vote_records),
    )

    return sim_run


def _extract_rating(text: str) -> float:
    """Extract numerical rating from agent response text."""
    import re

    patterns = [
        r"FINAL_RATING:\s*([-+]?\d+\.?\d*)",
        r"RATING:\s*([-+]?\d+\.?\d*)",
        r"rating.*?([-+]?\d+\.?\d*)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            return max(-10, min(10, val))
    return 0.0


def _extract_confidence(text: str) -> float:
    """Extract confidence score from agent response text."""
    import re

    patterns = [
        r"CONFIDENCE:\s*(0?\.\d+|1\.0|1)",
        r"confidence.*?(0?\.\d+|1\.0)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            return max(0, min(1, val))
    return 0.5
