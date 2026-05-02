from __future__ import annotations

import structlog
from celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="tasks.discovery_tasks.trigger_weekly_scrape")
def trigger_weekly_scrape():
    """Trigger the weekly grant discovery scrape via the discovery service."""
    import httpx
    from config import settings

    logger.info("Triggering weekly discovery scrape")
    try:
        resp = httpx.post("http://discovery-service:8002/v1/scrape/trigger", timeout=10)
        resp.raise_for_status()
        logger.info("Discovery scrape triggered", status=resp.status_code)
    except Exception as e:
        logger.error("Failed to trigger discovery scrape", error=str(e))
