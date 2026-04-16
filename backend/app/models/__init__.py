from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from app.models.article import Article  # noqa: E402, F401
from app.models.trend import Trend, TrendArticle  # noqa: E402, F401
from app.models.chain import EffectChain, ChainLink  # noqa: E402, F401
from app.models.stock_cache import StockCache  # noqa: E402, F401
from app.models.prediction import Prediction  # noqa: E402, F401
from app.models.simulation import SimulationRun, AgentVote  # noqa: E402, F401
from app.models.accuracy import PredictionAccuracy  # noqa: E402, F401
