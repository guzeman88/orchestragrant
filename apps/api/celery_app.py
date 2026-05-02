from __future__ import annotations

from celery import Celery
from config import settings

celery_app = Celery(
    "orchestragrant",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "tasks.document_tasks",
        "tasks.email_tasks",
        "tasks.discovery_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "deadline-reminders-daily": {
            "task": "tasks.email_tasks.send_deadline_reminders",
            "schedule": 86400,  # every 24 hours
        },
        "discovery-scrape-weekly": {
            "task": "tasks.discovery_tasks.trigger_weekly_scrape",
            "schedule": 604800,  # every 7 days
        },
    },
)
