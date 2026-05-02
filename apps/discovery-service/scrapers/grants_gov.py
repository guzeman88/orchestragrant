"""Grants.gov SEARCH API v2 client for discovering arts-related federal grants."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

GRANTS_GOV_BASE = "https://apply07.grants.gov/grantsws/rest/opportunities/search"

# Arts-relevant CFDA prefixes / agency codes
ARTS_AGENCIES = ["45"]  # NEA=45.024, NEH=45.xxx, others
ARTS_KEYWORDS = [
    "performing arts", "orchestra", "symphony", "music", "dance", "theater",
    "arts education", "cultural arts", "visual arts", "opera", "classical music",
]


@dataclass
class RawGrant:
    external_id: str
    source: str
    title: str
    description: str | None
    eligibility: str | None
    funder_name: str
    funder_type: str
    grant_type: str | None
    min_amount: float | None
    max_amount: float | None
    deadline: date | None
    open_date: date | None
    url: str | None
    arts_specific: bool


def _parse_date(s: str | None) -> date | None:
    if not s:
        return None
    for fmt in ("%m%d%Y", "%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _classify_amount(opportunity: dict[str, Any]) -> tuple[float | None, float | None]:
    award_floor = opportunity.get("awardFloor")
    award_ceiling = opportunity.get("awardCeiling")
    est_total = opportunity.get("estimatedTotalProgramFunding")
    try:
        min_amt = float(award_floor) if award_floor else None
    except (TypeError, ValueError):
        min_amt = None
    try:
        max_amt = float(award_ceiling) if award_ceiling else (float(est_total) if est_total else None)
    except (TypeError, ValueError):
        max_amt = None
    return min_amt, max_amt


def _is_arts_relevant(opp: dict[str, Any]) -> bool:
    searchable = " ".join([
        str(opp.get("title", "")),
        str(opp.get("synopsis", "")),
        str(opp.get("agencyName", "")),
        " ".join(str(c) for c in (opp.get("cfdaList") or [])),
    ]).lower()
    return any(kw in searchable for kw in ARTS_KEYWORDS)


async def fetch_arts_grants(api_key: str, max_pages: int = 20, page_size: int = 25) -> list[RawGrant]:
    """Fetch arts-relevant grants from Grants.gov and return as RawGrant objects."""
    results: list[RawGrant] = []

    async with httpx.AsyncClient(timeout=30) as client:
        for page in range(0, max_pages):
            params = {
                "keyword": "performing arts music symphony orchestra",
                "oppStatuses": "forecasted|posted",
                "rows": page_size,
                "startRecordNum": page * page_size,
                "apiKey": api_key,
            }
            try:
                res = await client.get(GRANTS_GOV_BASE, params=params)
                res.raise_for_status()
                data = res.json()
            except Exception as exc:
                logger.error("Grants.gov fetch error", page=page, error=str(exc))
                break

            opportunities = data.get("oppHits", [])
            if not opportunities:
                break

            for opp in opportunities:
                if not _is_arts_relevant(opp):
                    continue

                min_amt, max_amt = _classify_amount(opp)

                results.append(RawGrant(
                    external_id=f"ggov-{opp.get('id', '')}",
                    source="grants_gov",
                    title=opp.get("title", "Untitled"),
                    description=opp.get("synopsis"),
                    eligibility=opp.get("eligibilities"),
                    funder_name=opp.get("agencyName", "Federal Government"),
                    funder_type="government_federal",
                    grant_type="project",
                    min_amount=min_amt,
                    max_amount=max_amt,
                    deadline=_parse_date(opp.get("closeDate")),
                    open_date=_parse_date(opp.get("openDate")),
                    url=f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={opp.get('id')}",
                    arts_specific=True,
                ))

            total = data.get("hitCount", 0)
            fetched_so_far = (page + 1) * page_size
            if fetched_so_far >= total:
                break

    logger.info("Grants.gov fetch complete", count=len(results))
    return results
