"""Stripe webhook handler.

Validates stripe-signature and processes subscription lifecycle events.
Route is intentionally NOT behind JWT auth — Stripe posts here directly.
Signature validation replaces auth.
"""
from __future__ import annotations

import stripe
import structlog
from fastapi import APIRouter, Header, HTTPException, Request, status

from config import settings
from database import get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def _construct_event(payload: bytes, sig: str) -> stripe.Event:
    """Raise stripe.error.SignatureVerificationError if invalid."""
    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=sig,
        secret=settings.STRIPE_WEBHOOK_SECRET,
    )


# ── Tier mapping ──────────────────────────────────────────────────────────────

_PRICE_TO_TIER: dict[str, str] = {
    # Populated from Stripe dashboard price IDs in .env
}

def _tier_from_subscription(subscription: stripe.Subscription) -> str:
    """Derive org tier name from first subscription item's price ID."""
    items = subscription.get("items", {}).get("data", [])
    if not items:
        return "starter"
    price_id = items[0]["price"]["id"]
    return _PRICE_TO_TIER.get(price_id, "starter")


# ── Event handlers ────────────────────────────────────────────────────────────

async def _handle_checkout_completed(session: dict):
    """checkout.session.completed — provision subscription after payment."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from models import Organization

    org_id: str | None = (session.get("metadata") or {}).get("org_id")
    customer_id: str = session.get("customer", "")
    subscription_id: str = session.get("subscription", "")

    if not org_id:
        logger.warning("checkout.session.completed missing org_id metadata")
        return

    # Retrieve subscription to determine tier
    sub = stripe.Subscription.retrieve(subscription_id)
    tier = _tier_from_subscription(sub)
    interval = sub["items"]["data"][0]["price"].get("recurring", {}).get("interval", "month")

    async for db in get_db():
        result = await db.execute(select(Organization).where(Organization.id == org_id))
        org = result.scalar_one_or_none()
        if not org:
            logger.warning("Org not found for checkout", org_id=org_id)
            return
        org.stripe_customer_id = customer_id
        org.stripe_subscription_id = subscription_id
        org.subscription_tier = tier
        org.subscription_status = "active"
        org.billing_interval = interval
        await db.flush()
        logger.info("Subscription provisioned", org_id=org_id, tier=tier)


async def _handle_subscription_updated(subscription: dict):
    """customer.subscription.updated — update tier/status."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from models import Organization

    sub_id = subscription.get("id", "")
    new_status = subscription.get("status", "active")
    tier = _tier_from_subscription(subscription)  # type: ignore[arg-type]

    async for db in get_db():
        result = await db.execute(
            select(Organization).where(Organization.stripe_subscription_id == sub_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            return
        org.subscription_tier = tier
        org.subscription_status = new_status
        await db.flush()
        logger.info("Subscription updated", sub_id=sub_id, tier=tier, status=new_status)


async def _handle_subscription_deleted(subscription: dict):
    """customer.subscription.deleted — downgrade org to free tier."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from models import Organization

    sub_id = subscription.get("id", "")

    async for db in get_db():
        result = await db.execute(
            select(Organization).where(Organization.stripe_subscription_id == sub_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            return
        org.subscription_tier = "free"
        org.subscription_status = "cancelled"
        org.stripe_subscription_id = None
        await db.flush()
        logger.info("Subscription cancelled — org downgraded to free", sub_id=sub_id)


async def _handle_payment_failed(invoice: dict):
    """invoice.payment_failed — mark subscription as past_due."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from models import Organization

    sub_id = invoice.get("subscription", "")
    if not sub_id:
        return

    async for db in get_db():
        result = await db.execute(
            select(Organization).where(Organization.stripe_subscription_id == sub_id)
        )
        org = result.scalar_one_or_none()
        if not org:
            return
        org.subscription_status = "past_due"
        await db.flush()
        logger.warning("Invoice payment failed — org marked past_due", sub_id=sub_id, org_id=str(org.id))


# ── Router ────────────────────────────────────────────────────────────────────

@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(..., alias="stripe-signature"),
):
    """Receive and validate Stripe webhook events."""
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Stripe webhooks not configured")

    payload = await request.body()

    try:
        event = _construct_event(payload, stripe_signature)
    except stripe.error.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type: str = event["type"]
    data_obj: dict = event["data"]["object"]

    logger.info("Stripe webhook received", event_type=event_type, event_id=event["id"])

    try:
        if event_type == "checkout.session.completed":
            await _handle_checkout_completed(data_obj)
        elif event_type == "customer.subscription.updated":
            await _handle_subscription_updated(data_obj)
        elif event_type == "customer.subscription.deleted":
            await _handle_subscription_deleted(data_obj)
        elif event_type == "invoice.payment_failed":
            await _handle_payment_failed(data_obj)
        else:
            logger.debug("Unhandled Stripe event type", event_type=event_type)
    except Exception as exc:
        # Log but return 200 to prevent Stripe retries for application errors
        logger.error("Stripe webhook handler error", event_type=event_type, error=str(exc))

    return {"received": True}
