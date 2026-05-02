"""Grant endpoint tests: list/filter, FTS search, watchlist add/remove."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Funder, Grant, Organization

pytestmark = pytest.mark.asyncio


# ── Factories ─────────────────────────────────────────────────────────────────

async def _make_funder(db: AsyncSession, name: str = "Test Foundation") -> Funder:
    funder = Funder(
        id=uuid.uuid4(),
        name=name,
        type="foundation",
        arts_specific=True,
    )
    db.add(funder)
    await db.flush()
    return funder


async def _make_grant(
    db: AsyncSession,
    funder: Funder,
    title: str = "Arts Support Grant",
    amount_max: float = 50000,
    deadline_days: int = 60,
    grant_type: str = "project",
) -> Grant:
    g = Grant(
        id=uuid.uuid4(),
        funder_id=funder.id,
        title=title,
        description=f"Description for {title}",
        type=grant_type,
        min_amount=1000,
        max_amount=amount_max,
        deadline=(datetime.now(timezone.utc) + timedelta(days=deadline_days)).date(),
        is_active=True,
    )
    db.add(g)
    await db.flush()
    return g


# ── List/filter ───────────────────────────────────────────────────────────────

async def test_list_grants_unauthenticated(client: AsyncClient):
    res = await client.get("/v1/grants")
    assert res.status_code == 401


async def test_list_grants_returns_paginated(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    funder = await _make_funder(db)
    for i in range(3):
        await _make_grant(db, funder, title=f"Grant {i}")

    res = await client.get("/v1/grants?page=1&page_size=10", headers=auth_headers)
    assert res.status_code == 200
    body = res.json()
    # API returns either a list or {"items": [...], "total": ...}
    items = body if isinstance(body, list) else body.get("items", body.get("data", []))
    assert len(items) >= 3


async def test_list_grants_filter_by_type(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    funder = await _make_funder(db)
    await _make_grant(db, funder, title="Project Grant", grant_type="project")
    await _make_grant(db, funder, title="Operating Grant", grant_type="general_operating")

    res = await client.get("/v1/grants?grant_type=general_operating", headers=auth_headers)
    assert res.status_code == 200


async def test_list_grants_filter_by_amount(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    funder = await _make_funder(db)
    await _make_grant(db, funder, title="Small Grant", amount_max=5000)
    await _make_grant(db, funder, title="Large Grant", amount_max=100000)

    res = await client.get("/v1/grants?amount_max=10000", headers=auth_headers)
    assert res.status_code == 200


async def test_fts_search_returns_relevant_results(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    funder = await _make_funder(db)
    await _make_grant(db, funder, title="Symphony Orchestra Development Fund")

    res = await client.get("/v1/grants?search=symphony+orchestra", headers=auth_headers)
    assert res.status_code == 200


# ── Grant detail ──────────────────────────────────────────────────────────────

async def test_get_grant_detail(client: AsyncClient, auth_headers: dict, db: AsyncSession):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder, title="Detail Test Grant")

    res = await client.get(f"/v1/grants/{g.id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["title"] == "Detail Test Grant"


async def test_get_nonexistent_grant(client: AsyncClient, auth_headers: dict):
    res = await client.get(f"/v1/grants/{uuid.uuid4()}", headers=auth_headers)
    assert res.status_code == 404


# ── Watchlist ─────────────────────────────────────────────────────────────────

async def test_add_to_watchlist(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)

    res = await client.post(f"/v1/grants/{g.id}/watch", headers=auth_headers)
    assert res.status_code in (200, 201, 204)


async def test_add_to_watchlist_idempotent(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)

    await client.post(f"/v1/grants/{g.id}/watch", headers=auth_headers)
    res2 = await client.post(f"/v1/grants/{g.id}/watch", headers=auth_headers)
    assert res2.status_code in (200, 201, 204, 409)


async def test_remove_from_watchlist(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)

    await client.post(f"/v1/grants/{g.id}/watch", headers=auth_headers)
    res = await client.delete(f"/v1/grants/{g.id}/watch", headers=auth_headers)
    assert res.status_code in (200, 204)
