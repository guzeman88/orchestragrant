from __future__ import annotations

import boto3
from botocore.exceptions import BotoCoreError, ClientError
import structlog
from jinja2 import Environment, PackageLoader, select_autoescape

from config import settings

logger = structlog.get_logger(__name__)

_ses = None
_jinja: Environment | None = None


def _get_ses():
    global _ses
    if _ses is None:
        _ses = boto3.client(
            "ses",
            region_name=settings.AWS_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
    return _ses


def _get_jinja() -> Environment:
    global _jinja
    if _jinja is None:
        import os
        from jinja2 import FileSystemLoader
        templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "email")
        _jinja = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html"]),
        )
    return _jinja


def render_template(template_name: str, **context: object) -> tuple[str, str]:
    """Return (subject, html_body) rendered from Jinja2 templates."""
    env = _get_jinja()
    tmpl = env.get_template(template_name)
    rendered = tmpl.render(**context)
    # Templates embed subject in a comment: {# subject: My Subject #}
    subject = "OrchestraGrant Notification"
    for line in rendered.splitlines():
        stripped = line.strip()
        if stripped.startswith("{#") and "subject:" in stripped:
            subject = stripped.split("subject:", 1)[1].strip().rstrip("#}").strip()
            break
    return subject, rendered


def send_email(
    to: str | list[str],
    template_name: str,
    **template_context: object,
) -> bool:
    """Send a transactional email via AWS SES. Returns True on success."""
    if settings.ENV in ("test", "development") and not settings.AWS_ACCESS_KEY_ID:
        logger.info("Email skipped (dev mode)", template=template_name, to=to)
        return True

    if isinstance(to, str):
        to = [to]

    subject, html_body = render_template(template_name, **template_context)

    # Plain-text fallback by stripping tags (rough but good enough)
    import re
    text_body = re.sub(r"<[^>]+>", "", html_body).strip()

    try:
        _get_ses().send_email(
            Source=settings.SES_FROM_ADDRESS,
            Destination={"ToAddresses": to},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
        logger.info("Email sent", template=template_name, recipients=to)
        return True
    except (BotoCoreError, ClientError) as exc:
        logger.error("SES send failed", error=str(exc), template=template_name, recipients=to)
        return False
