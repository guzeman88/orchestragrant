from __future__ import annotations

import structlog
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/scrape", tags=["discovery"])


class ScrapeResult(BaseModel):
    triggered: bool
    message: str


class ScrapeStats(BaseModel):
    grants_found: int
    new: int
    updated: int
    sources: dict


@router.post("/trigger", response_model=ScrapeResult)
async def trigger_scrape(background_tasks: BackgroundTasks):
    """Trigger a background grant discovery scrape (non-blocking)."""
    background_tasks.add_task(_run_scrape)
    logger.info("Grant discovery scrape triggered")
    return ScrapeResult(triggered=True, message="Scrape job enqueued")


@router.post("/run", response_model=ScrapeStats)
async def run_scrape_sync():
    """Run a full grant discovery scrape synchronously (for scheduled jobs)."""
    from pipeline import run_all
    result = await run_all()
    return ScrapeStats(**result)


async def _run_scrape():
    """Background task wrapper for the full pipeline."""
    from pipeline import run_all
    try:
        await run_all()
    except Exception as exc:
        logger.error("Background scrape failed", error=str(exc))
