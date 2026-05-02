"""Candid (Foundation Directory) API client for foundation/private grant discovery."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx
import structlog

from scrapers.grants_gov import RawGrant

logger = structlog.get_logger(__name__)

CANDID_TOKEN_URL = "https://api.candid.org/grants/v1/auth/token"
CANDID_GRANTS_URL = "https://api.candid.org/grants/v1/search"

ARTS_SUBJECT_CODES = [
    "A",   # Arts, Culture, Humanities (general)
    "A01", "A02", "A03", "A04", "A05", "A06", "A07", "A30",
]


async def _get_access_token(client_id: str, client_secret: str) -> str | None:
    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.post(
            CANDID_TOKEN_URL,
            json={"client_id": client_id, "client_secret": client_secret},
        )
        if res.status_code == 200:
            return res.json().get("access_token")
    logger.warning("Candid auth failed — skipping Candid source")
    return None


async def fetch_foundation_grants(
    client_id: str,
    client_secret: str,
    max_results: int = 200,
) -> list[RawGrant]:
    """Fetch arts foundation grants from Candid API."""
    if not client_id or not client_secret:
        logger.info("Candid credentials not configured — skipping")
        return []

    token = await _get_access_token(client_id, client_secret)
    if not token:
        return []

    results: list[RawGrant] = []
    page = 1

    async with httpx.AsyncClient(
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    ) as client:
        while len(results) < max_results:
            payload: dict[str, Any] = {
                "subject_codes": ARTS_SUBJECT_CODES,
                "recipient_type": ["Public Charity"],
                "fields": [
                    "grant_id", "grant_name", "grant_description",
                    "funder_name", "funder_type",
                    "grant_amount_min", "grant_amount_max",
                    "deadline_date", "open_date",
                    "application_url", "eligibility_description",
                ],
                "page": page,
                "page_size": min(50, max_results - len(results)),
            }
            try:
                res = await client.post(CANDID_GRANTS_URL, json=payload)
                res.raise_for_status()
                data = res.json()
            except Exception as exc:
                logger.error("Candid API error", page=page, error=str(exc))
                break

            grants = data.get("grants", [])
            if not grants:
                break

            for g in grants:
                deadline_str = g.get("deadline_date")
                open_str = g.get("open_date")
                try:
                    deadline = datetime.fromisoformat(deadline_str).date() if deadline_str else None
                except ValueError:
                    deadline = None
                try:
                    open_date = datetime.fromisoformat(open_str).date() if open_str else None
                except ValueError:
                    open_date = None

                results.append(RawGrant(
                    external_id=f"candid-{g.get('grant_id', '')}",
                    source="candid",
                    title=g.get("grant_name", "Untitled Foundation Grant"),
                    description=g.get("grant_description"),
                    eligibility=g.get("eligibility_description"),
                    funder_name=g.get("funder_name", "Private Foundation"),
                    funder_type=g.get("funder_type", "foundation"),
                    grant_type="project",
                    min_amount=g.get("grant_amount_min"),
                    max_amount=g.get("grant_amount_max"),
                    deadline=deadline,
                    open_date=open_date,
                    url=g.get("application_url"),
                    arts_specific=True,
                ))

            total = data.get("total_count", 0)
            if len(results) >= total:
                break
            page += 1

    logger.info("Candid fetch complete", count=len(results))
    return results
