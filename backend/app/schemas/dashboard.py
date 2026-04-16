from pydantic import BaseModel

from app.schemas.prediction import SignalResponse


class DashboardSummary(BaseModel):
    total_predictions: int
    active_signals: int
    accuracy_rate: float | None  # percentage
    accuracy_count: int
    top_signals: list[SignalResponse]
    recent_predictions: list[SignalResponse]
    scheduler_status: dict


class AccuracyMetrics(BaseModel):
    total_evaluated: int
    direction_correct_1d: float | None
    direction_correct_3d: float | None
    direction_correct_5d: float | None
    significant_moves_hit: float | None
    avg_max_move_pct: float | None
