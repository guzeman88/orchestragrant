"""Pipeline orchestrator: runs all scrapers, deduplicates, upserts into grants DB."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy import create_engine, text, select
from sqlalchemy.orm import Session

from config import settings
from scrapers.grants_gov import RawGrant, fetch_arts_grants
from scrapers.candid import fetch_foundation_grants
from scrapers.web_scraper import scrape_all_web_sources

logger = structlog.get_logger(__name__)

# ── DB helpers ────────────────────────────────────────────────────────────────

UPSERT_FUNDER_SQL = text("""
    INSERT INTO grants.funders (id, name, funder_type, created_at, updated_at)
    VALUES (:id, :name, :funder_type, now(), now())
    ON CONFLICT (name) DO UPDATE
        SET funder_type = EXCLUDED.funder_type,
            updated_at  = now()
    RETURNING id
""")

UPSERT_GRANT_SQL = text("""
    INSERT INTO grants.grants (
        id, funder_id, external_id, source, title, description,
        eligibility_notes, grant_type,
        amount_min, amount_max,
        deadline_at, open_at,
        application_url, is_arts_specific,
        created_at, updated_at
    )
    VALUES (
        :id, :funder_id, :external_id, :source, :title, :description,
        :eligibility, :grant_type,
        :min_amount, :max_amount,
        :deadline, :open_date,
        :url, :arts_specific,
        now(), now()
    )
    ON CONFLICT (external_id) DO UPDATE
        SET title         = EXCLUDED.title,
            description   = EXCLUDED.description,
            amount_min    = EXCLUDED.amount_min,
            amount_max    = EXCLUDED.amount_max,
            deadline_at   = EXCLUDED.deadline_at,
            open_at       = EXCLUDED.open_at,
            updated_at    = now()
    RETURNING id, (xmax = 0) AS inserted
""")

INSERT_SCRAPE_RUN_SQL = text("""
    INSERT INTO discovery.scrape_runs (
        id, source, status, grants_found, grants_new, grants_updated,
        started_at, finished_at
    )
    VALUES (
        :id, :source, :status, :grants_found, :grants_new, :grants_updated,
        :started_at, :finished_at
    )
""")


def _funder_id_for(name: str) -> str:
    """Deterministic UUID v5 for funder name."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"funder:{name.lower()}"))


def _grant_id_for(external_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"grant:{external_id}"))


def upsert_grants(db: Session, grants: list[RawGrant]) -> dict[str, int]:
    """Upsert grants and their funders. Returns stats."""
    new_count = 0
    updated_count = 0

    # Group by funder to batch funder upserts
    funder_ids: dict[str, str] = {}
    for g in grants:
        fname = g.funder_name
        if fname not in funder_ids:
            fid = _funder_id_for(fname)
            row = db.execute(
                UPSERT_FUNDER_SQL,
                {"id": fid, "name": fname, "funder_type": g.funder_type},
            ).fetchone()
            funder_ids[fname] = str(row[0])

    for g in grants:
        funder_id = funder_ids[g.funder_name]
        grant_id = _grant_id_for(g.external_id)
        row = db.execute(
            UPSERT_GRANT_SQL,
            {
                "id": grant_id,
                "funder_id": funder_id,
                "external_id": g.external_id,
                "source": g.source,
                "title": g.title,
                "description": g.description,
                "eligibility": g.eligibility,
                "grant_type": g.grant_type,
                "min_amount": g.min_amount,
                "max_amount": g.max_amount,
                "deadline": g.deadline,
                "open_date": g.open_date,
                "url": g.url,
                "arts_specific": g.arts_specific,
            },
        ).fetchone()
        if row and row[1]:  # inserted = True
            new_count += 1
        else:
            updated_count += 1

    db.commit()
    return {"new": new_count, "updated": updated_count}


def record_scrape_run(
    db: Session,
    source: str,
    grants_found: int,
    new: int,
    updated: int,
    started_at: datetime,
    error: str | None = None,
):
    db.execute(
        INSERT_SCRAPE_RUN_SQL,
        {
            "id": str(uuid.uuid4()),
            "source": source,
            "status": "failed" if error else "complete",
            "grants_found": grants_found,
            "grants_new": new,
            "grants_updated": updated,
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc),
        },
    )
    db.commit()


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_all() -> dict[str, Any]:
    """
    Full discovery pipeline:
    1. Fetch from Grants.gov
    2. Fetch from Candid
    3. Playwright web scrapes (NEA, state councils)
    4. Deduplicate by external_id across sources
    5. Upsert into grants DB
    6. Record scrape run stats
    """
    started_at = datetime.now(timezone.utc)
    summary: dict[str, Any] = {}

    if not settings.DATABASE_URL_SYNC:
        logger.error("DATABASE_URL_SYNC not configured — cannot persist grants")
        return {"error": "no_db"}

    engine = create_engine(settings.DATABASE_URL_SYNC)

    # ── 1. Gather from all sources ────────────────────────────────────────────
    ggov_grants: list[RawGrant] = []
    candid_grants: list[RawGrant] = []
    web_grants: list[RawGrant] = []

    try:
        ggov_grants = await fetch_arts_grants(
            api_key=settings.GRANTS_GOV_API_KEY,
            max_pages=settings.GRANTS_GOV_MAX_PAGES,
            page_size=settings.GRANTS_GOV_PAGE_SIZE,
        )
    except Exception as exc:
        logger.error("Grants.gov pipeline error", error=str(exc))

    try:
        candid_grants = await fetch_foundation_grants(
            client_id=settings.CANDID_CLIENT_ID,
            client_secret=settings.CANDID_CLIENT_SECRET,
            max_results=settings.CANDID_MAX_RESULTS,
        )
    except Exception as exc:
        logger.error("Candid pipeline error", error=str(exc))

    try:
        web_grants = await scrape_all_web_sources()
    except Exception as exc:
        logger.error("Web scraper pipeline error", error=str(exc))

    # ── 2. Deduplicate by external_id ─────────────────────────────────────────
    seen: set[str] = set()
    all_grants: list[RawGrant] = []
    for g in ggov_grants + candid_grants + web_grants:
        if g.external_id not in seen:
            seen.add(g.external_id)
            all_grants.append(g)

    logger.info(
        "Discovery pipeline — grants collected",
        total=len(all_grants),
        grants_gov=len(ggov_grants),
        candid=len(candid_grants),
        web=len(web_grants),
    )

    # ── 3. Upsert ─────────────────────────────────────────────────────────────
    with Session(engine) as db:
        stats = upsert_grants(db, all_grants)
        record_scrape_run(
            db,
            source="all",
            grants_found=len(all_grants),
            new=stats["new"],
            updated=stats["updated"],
            started_at=started_at,
        )

    engine.dispose()

    summary = {
        "grants_found": len(all_grants),
        "new": stats["new"],
        "updated": stats["updated"],
        "sources": {
            "grants_gov": len(ggov_grants),
            "candid": len(candid_grants),
            "web": len(web_grants),
        },
    }
    logger.info("Discovery pipeline complete", **summary)
    return summary
