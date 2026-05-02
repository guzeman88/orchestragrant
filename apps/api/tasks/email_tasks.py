from __future__ import annotations

from datetime import datetime, timezone

import structlog
from celery_app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(name="tasks.email_tasks.send_deadline_reminders")
def send_deadline_reminders():
    """Find deadlines with reminders due today and send notification emails to all org users."""
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session, joinedload
    from config import settings
    from models import Deadline, User, Organization
    from services.email_service import send_email

    logger.info("Running deadline reminder job")
    engine = create_engine(settings.DATABASE_URL_SYNC)
    today = datetime.now(timezone.utc).date()
    year = today.year
    base_url = settings.APP_BASE_URL if hasattr(settings, "APP_BASE_URL") else "https://app.orchestragrant.com"

    with Session(engine) as db:
        stmt = (
            select(Deadline)
            .where(Deadline.is_completed == False)
            .options(joinedload(Deadline.org).joinedload(Organization.users))
        )
        deadlines = db.execute(stmt).unique().scalars().all()

        reminders_sent = 0
        for deadline in deadlines:
            deadline_date = deadline.deadline_at.date()
            days_until = (deadline_date - today).days
            if days_until not in (deadline.reminder_days or []):
                continue

            org = deadline.org
            if not org:
                continue

            active_users = [u for u in org.users if u.is_active]
            deadline_date_str = deadline.deadline_at.strftime("%B %-d, %Y")

            for user in active_users:
                send_email(
                    to=user.email,
                    template_name="deadline_reminder.html",
                    first_name=user.first_name,
                    org_name=org.name,
                    deadline_title=deadline.title,
                    deadline_date=deadline_date_str,
                    days_until=days_until,
                    application_id=str(deadline.application_id) if deadline.application_id else None,
                    app_url=f"{base_url}/applications/{deadline.application_id}" if deadline.application_id else "",
                    dashboard_url=f"{base_url}/dashboard",
                    unsubscribe_url=f"{base_url}/settings/notifications",
                    year=year,
                )
                reminders_sent += 1
                logger.info("Reminder sent", deadline_id=str(deadline.id), user_id=str(user.id))

    engine.dispose()
    logger.info("Deadline reminder job complete", reminders_sent=reminders_sent)


@celery_app.task(name="tasks.email_tasks.send_invite_email", bind=True, max_retries=3)
def send_invite_email(self, user_id: str, invite_url: str, temp_password: str):
    """Send a user invite email via AWS SES."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from config import settings
    from models import User, Organization
    from services.email_service import send_email
    from datetime import date

    logger.info("Sending invite email", user_id=user_id)
    engine = create_engine(settings.DATABASE_URL_SYNC)

    try:
        with Session(engine) as db:
            user = db.get(User, user_id)
            if not user:
                logger.warning("User not found for invite email", user_id=user_id)
                return

            org = db.get(Organization, user.org_id)
            invited_by = None
            if user.invited_by:
                invited_by = db.get(User, user.invited_by)

            success = send_email(
                to=user.email,
                template_name="invite.html",
                first_name=user.first_name,
                org_name=org.name if org else "your organization",
                invited_by_name=f"{invited_by.first_name} {invited_by.last_name}" if invited_by else "OrchestraGrant",
                invite_url=invite_url,
                temp_password=temp_password,
                year=date.today().year,
            )
            if not success:
                raise RuntimeError("SES delivery failed")
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        engine.dispose()
