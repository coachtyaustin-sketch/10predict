import asyncio

from fastapi import APIRouter, BackgroundTasks

from app.services.research_cycle import run_research_cycle

router = APIRouter()

# Track running cycles to prevent overlaps
_running_cycle = False


@router.post("/trigger")
async def trigger_research_cycle(
    cycle_type: str = "manual",
    background_tasks: BackgroundTasks = None,
):
    """Manually trigger a research cycle."""
    global _running_cycle
    if _running_cycle:
        return {"status": "already_running", "message": "A research cycle is already in progress"}

    _running_cycle = True

    async def _run():
        global _running_cycle
        try:
            result = await run_research_cycle(cycle_type)
            return result
        finally:
            _running_cycle = False

    # Run in background so the endpoint returns immediately
    background_tasks.add_task(_run)

    return {
        "status": "started",
        "cycle_type": cycle_type,
        "message": "Research cycle started in background",
    }


@router.get("/status")
async def research_status():
    """Check if a research cycle is currently running."""
    return {"running": _running_cycle}
