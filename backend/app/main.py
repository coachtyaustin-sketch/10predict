from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings
from app.dependencies import init_db, shutdown_db, init_neo4j, shutdown_neo4j
from app.scheduler.scheduler import start_scheduler, shutdown_scheduler

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("Starting 10Predict", version="0.1.0")
    await init_db()
    await init_neo4j()
    start_scheduler()
    logger.info("10Predict ready")
    yield
    shutdown_scheduler()
    await shutdown_neo4j()
    await shutdown_db()
    logger.info("10Predict shutdown complete")


app = FastAPI(
    title="10Predict",
    description="Chain-of-effects penny stock prediction using swarm intelligence",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
