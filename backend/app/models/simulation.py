import datetime
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class SimulationRun(Base):
    """Record of a swarm simulation run for a stock prediction."""

    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    prediction_id: Mapped[int | None] = mapped_column(
        ForeignKey("predictions.id"), nullable=True
    )
    ticker: Mapped[str] = mapped_column(String(10), index=True)
    chain_id: Mapped[int] = mapped_column(ForeignKey("effect_chains.id"))

    agent_count: Mapped[int] = mapped_column(Integer)
    round_count: Mapped[int] = mapped_column(Integer)
    duration_seconds: Mapped[float] = mapped_column(Float, default=0)

    # Raw simulation data
    seed_post: Mapped[str] = mapped_column(Text)
    transcript: Mapped[dict] = mapped_column(JSONB, default=list)  # all posts/comments
    agent_votes: Mapped[dict] = mapped_column(JSONB, default=dict)  # per-agent final vote

    # Aggregated results
    weighted_vote: Mapped[float] = mapped_column(Float, default=0)
    sentiment_score: Mapped[float] = mapped_column(Float, default=0)
    consensus_strength: Mapped[float] = mapped_column(Float, default=0)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class AgentVote(Base):
    """Individual agent's final position from a simulation."""

    __tablename__ = "agent_votes"

    id: Mapped[int] = mapped_column(primary_key=True)
    simulation_id: Mapped[int] = mapped_column(ForeignKey("simulation_runs.id"))
    agent_persona: Mapped[str] = mapped_column(String(100))  # bull_analyst, bear_analyst, etc.
    agent_name: Mapped[str] = mapped_column(String(200))
    initial_position: Mapped[float] = mapped_column(Float)  # -10 to +10
    final_position: Mapped[float] = mapped_column(Float)  # -10 to +10
    confidence: Mapped[float] = mapped_column(Float)  # 0 to 1
    reasoning: Mapped[str] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, default=1.0)  # persona type weight
