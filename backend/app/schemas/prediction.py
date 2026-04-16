import datetime
from pydantic import BaseModel


class PredictionResponse(BaseModel):
    id: int
    ticker: str
    signal: str
    score: float
    confidence: float
    chain_depth: int
    chain_narrative: str
    why_most_miss_it: str
    bull_case: str
    bear_case: str
    key_catalysts: list
    risk_factors: list
    price_at_prediction: float
    target_price_low: float | None
    target_price_high: float | None
    timeframe_days: int
    cycle_type: str
    report_text: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class PredictionSummary(BaseModel):
    id: int
    ticker: str
    signal: str
    score: float
    confidence: float
    chain_narrative: str
    price_at_prediction: float
    cycle_type: str
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class SignalResponse(BaseModel):
    id: int
    ticker: str
    signal: str
    score: float
    confidence: float
    chain_narrative: str
    why_most_miss_it: str
    price_at_prediction: float
    chain_depth: int
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
