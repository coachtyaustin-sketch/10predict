"""APScheduler configuration for 3x daily research cycles."""

import asyncio

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.services.research_cycle import run_research_cycle

logger = structlog.get_logger()

_scheduler: AsyncIOScheduler | None = None


def start_scheduler():
    """Initialize and start the scheduler with 3x daily research cycles."""
    global _scheduler

    _scheduler = AsyncIOScheduler(timezone=settings.timezone)

    # Pre-market cycle (6 AM ET default)
    _scheduler.add_job(
        _run_cycle,
        CronTrigger(
            hour=settings.cycle_premarket_hour,
            minute=0,
            day_of_week="mon-fri",
            timezone=settings.timezone,
        ),
        kwargs={"cycle_type": "pre_market"},
        id="pre_market_cycle",
        name="Pre-Market Research Cycle",
        misfire_grace_time=3600,
    )

    # Midday cycle (12 PM ET default)
    _scheduler.add_job(
        _run_cycle,
        CronTrigger(
            hour=settings.cycle_midday_hour,
            minute=0,
            day_of_week="mon-fri",
            timezone=settings.timezone,
        ),
        kwargs={"cycle_type": "midday"},
        id="midday_cycle",
        name="Midday Research Cycle",
        misfire_grace_time=3600,
    )

    # After-hours cycle (5 PM ET default)
    _scheduler.add_job(
        _run_cycle,
        CronTrigger(
            hour=settings.cycle_afterhours_hour,
            minute=0,
            day_of_week="mon-fri",
            timezone=settings.timezone,
        ),
        kwargs={"cycle_type": "after_hours"},
        id="after_hours_cycle",
        name="After-Hours Research Cycle",
        misfire_grace_time=3600,
    )

    _scheduler.start()
    logger.info(
        "Scheduler started",
        cycles=[
            f"Pre-Market @ {settings.cycle_premarket_hour}:00",
            f"Midday @ {settings.cycle_midday_hour}:00",
            f"After-Hours @ {settings.cycle_afterhours_hour}:00",
        ],
        timezone=settings.timezone,
    )


async def _run_cycle(cycle_type: str):
    """Wrapper to run a research cycle with error handling."""
    try:
        logger.info("Scheduled cycle starting", cycle_type=cycle_type)
        result = await run_research_cycle(cycle_type)
        logger.info("Scheduled cycle finished", cycle_type=cycle_type, result=result)
    except Exception as e:
        logger.error("Scheduled cycle FAILED", cycle_type=cycle_type, error=str(e))


def shutdown_scheduler():
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler shut down")


def get_scheduler_status() -> dict:
    """Get current scheduler status for the health endpoint."""
    if not _scheduler:
        return {"running": False, "jobs": []}

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })

    return {"running": _scheduler.running, "jobs": jobs}
