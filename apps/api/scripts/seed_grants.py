#!/usr/bin/env python3
"""
Seed initial grants data from the Grants.gov API into the database.

Usage:
    python seed_grants.py [--max-pages 20] [--env development]

Requires DATABASE_URL_SYNC in environment or .env file.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

# Add apps/api to path so models/config are importable
ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(ROOT / "apps" / "api"))
sys.path.insert(0, str(ROOT / "apps" / "discovery-service"))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import structlog
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from scrapers.grants_gov import fetch_arts_grants

logger = structlog.get_logger(__name__)


def _get_db_url() -> str:
    url = os.getenv("DATABASE_URL_SYNC") or os.getenv("DATABASE_URL", "")
    if not url:
        raise SystemExit(
            "DATABASE_URL_SYNC not set. Export it or add to .env:\n"
            "  DATABASE_URL_SYNC=postgresql://user:pass@localhost/orchestragrant"
        )
    # Swap asyncpg driver for psycopg2 (sync seed script)
    return url.replace("postgresql+asyncpg://", "postgresql://")


UPSERT_FUNDER = text("""
    INSERT INTO grants.funders (id, name, funder_type, created_at, updated_at)
    VALUES (gen_random_uuid(), :name, :funder_type::grants.funder_type, now(), now())
    ON CONFLICT (name) DO NOTHING
    RETURNING id
""")

SELECT_FUNDER = text("SELECT id FROM grants.funders WHERE name = :name LIMIT 1")

UPSERT_GRANT = text("""
    INSERT INTO grants.grants (
        id, funder_id, external_id, source, title, description,
        eligibility_notes, grant_type, amount_min, amount_max,
        deadline_at, open_at, application_url, is_arts_specific,
        status, created_at, updated_at
    )
    VALUES (
        gen_random_uuid(), :funder_id, :external_id, :source, :title, :description,
        :eligibility, :grant_type::grants.grant_type, :min_amount, :max_amount,
        :deadline, :open_date, :url, :arts_specific,
        'open', now(), now()
    )
    ON CONFLICT (external_id) DO UPDATE
        SET title        = EXCLUDED.title,
            description  = EXCLUDED.description,
            amount_max   = EXCLUDED.amount_max,
            deadline_at  = EXCLUDED.deadline_at,
            updated_at   = now()
""")


async def _fetch(max_pages: int, api_key: str) -> list:
    return await fetch_arts_grants(api_key=api_key, max_pages=max_pages, page_size=25)


def seed(max_pages: int = 20):
    db_url = _get_db_url()
    api_key = os.getenv("GRANTS_GOV_API_KEY", "")
    engine = create_engine(db_url, echo=False)

    logger.info("Fetching arts grants from Grants.gov", max_pages=max_pages)
    grants = asyncio.run(_fetch(max_pages, api_key))
    logger.info("Grants fetched", count=len(grants))

    inserted = 0
    skipped = 0

    with Session(engine) as db:
        funder_cache: dict[str, str] = {}

        for g in grants:
            # Ensure funder exists
            fname = g.funder_name
            if fname not in funder_cache:
                row = db.execute(UPSERT_FUNDER, {"name": fname, "funder_type": g.funder_type}).fetchone()
                if row:
                    funder_cache[fname] = str(row[0])
                else:
                    existing = db.execute(SELECT_FUNDER, {"name": fname}).fetchone()
                    if existing:
                        funder_cache[fname] = str(existing[0])
                    else:
                        logger.warning("Could not resolve funder", name=fname)
                        continue

            funder_id = funder_cache[fname]

            # Normalize grant_type: only values in the enum are safe
            grant_type_map = {
                "project": "project",
                "general_operating": "general_operating",
                "capital": "capital",
                "endowment": "endowment",
                "emergency": "emergency",
                "commissioning": "commissioning",
                "education": "education",
                "touring": "touring",
                "recording": "recording",
                "technical_assistance": "technical_assistance",
            }
            grant_type = grant_type_map.get(g.grant_type or "project", "project")

            try:
                db.execute(UPSERT_GRANT, {
                    "funder_id": funder_id,
                    "external_id": g.external_id,
                    "source": g.source,
                    "title": g.title[:500] if g.title else "Untitled",
                    "description": g.description,
                    "eligibility": g.eligibility,
                    "grant_type": grant_type,
                    "min_amount": g.min_amount,
                    "max_amount": g.max_amount,
                    "deadline": g.deadline,
                    "open_date": g.open_date,
                    "url": g.url,
                    "arts_specific": g.arts_specific,
                })
                inserted += 1
            except Exception as exc:
                logger.warning("Skipped grant", external_id=g.external_id, error=str(exc))
                skipped += 1

        db.commit()

    engine.dispose()
    logger.info("Seed complete", inserted=inserted, skipped=skipped)
    print(f"\nSeed complete: {inserted} grants upserted, {skipped} skipped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed grants from Grants.gov")
    parser.add_argument("--max-pages", type=int, default=20, help="Max pages to fetch (25 grants/page)")
    args = parser.parse_args()
    seed(max_pages=args.max_pages)
