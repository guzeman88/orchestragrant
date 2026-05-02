"""Application endpoint tests: CRUD, stage transitions, section locking."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Application, ApplicationSection, Funder, Grant, Organization, User

pytestmark = pytest.mark.asyncio


# ── Factories ─────────────────────────────────────────────────────────────────

async def _make_funder(db: AsyncSession) -> Funder:
    f = Funder(id=uuid.uuid4(), name=f"Funder-{uuid.uuid4().hex[:6]}", type="foundation")
    db.add(f)
    await db.flush()
    return f


async def _make_grant(db: AsyncSession, funder: Funder) -> Grant:
    g = Grant(
        id=uuid.uuid4(),
        funder_id=funder.id,
        title="Test Grant",
        type="project",
        max_amount=50000,
        deadline=datetime.now(timezone.utc).date() + timedelta(days=60),
        is_active=True,
    )
    db.add(g)
    await db.flush()
    return g


async def _make_application(
    db: AsyncSession,
    org: Organization,
    grant: Grant,
    stage: str = "prospecting",
) -> Application:
    app = Application(
        id=uuid.uuid4(),
        org_id=org.id,
        grant_id=grant.id,
        title=f"Application for {grant.title}",
        stage=stage,
        requested_amount=25000,
    )
    db.add(app)
    await db.flush()
    return app


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def test_create_application(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)

    res = await client.post(
        "/v1/applications",
        json={
            "grant_id": str(g.id),
            "title": "New Application",
            "requested_amount": 30000,
        },
        headers=auth_headers,
    )
    assert res.status_code == 201
    body = res.json()
    assert body["stage"] == "prospecting"
    assert body["title"] == "New Application"


async def test_list_applications(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    await _make_application(db, test_org, g)

    res = await client.get("/v1/applications", headers=auth_headers)
    assert res.status_code == 200
    items = res.json() if isinstance(res.json(), list) else res.json().get("items", [])
    assert len(items) >= 1


async def test_get_application_detail(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    app = await _make_application(db, test_org, g)

    res = await client.get(f"/v1/applications/{app.id}", headers=auth_headers)
    assert res.status_code == 200
    assert str(app.id) in res.json()["id"]


async def test_get_application_not_found(client: AsyncClient, auth_headers: dict):
    res = await client.get(f"/v1/applications/{uuid.uuid4()}", headers=auth_headers)
    assert res.status_code == 404


async def test_cannot_access_other_orgs_application(
    client: AsyncClient, auth_headers: dict, db: AsyncSession
):
    # Application belonging to a different org
    other_org = Organization(
        id=uuid.uuid4(),
        name="Other Org",
        legal_name="Other Org Inc.",
        ein="88-1234567",
        org_type="symphony",
        primary_email="other@test.com",
        address_state="NY",
    )
    db.add(other_org)
    await db.flush()

    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    other_app = await _make_application(db, other_org, g)

    res = await client.get(f"/v1/applications/{other_app.id}", headers=auth_headers)
    assert res.status_code in (403, 404)


# ── Stage transitions ─────────────────────────────────────────────────────────

VALID_TRANSITIONS = [
    ("prospecting", "qualifying"),
    ("qualifying", "writing"),
    ("writing", "internal_review"),
    ("internal_review", "director_review"),
    ("director_review", "board_approval"),
    ("board_approval", "ready_to_submit"),
    ("ready_to_submit", "submitted"),
]


@pytest.mark.parametrize("from_stage,to_stage", VALID_TRANSITIONS)
async def test_valid_stage_transition(
    client: AsyncClient,
    auth_headers: dict,
    db: AsyncSession,
    test_org: Organization,
    from_stage: str,
    to_stage: str,
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    app = await _make_application(db, test_org, g, stage=from_stage)

    res = await client.patch(
        f"/v1/applications/{app.id}",
        json={"stage": to_stage},
        headers=auth_headers,
    )
    assert res.status_code in (200, 204)


async def test_invalid_stage_transition_rejected(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    # Can't skip from prospecting to submitted
    app = await _make_application(db, test_org, g, stage="prospecting")

    res = await client.patch(
        f"/v1/applications/{app.id}",
        json={"stage": "submitted"},
        headers=auth_headers,
    )
    assert res.status_code in (400, 422)


async def test_submitted_application_immutable(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    app = await _make_application(db, test_org, g, stage="submitted")

    res = await client.patch(
        f"/v1/applications/{app.id}",
        json={"title": "Trying to edit submitted app"},
        headers=auth_headers,
    )
    assert res.status_code in (400, 403, 422)


# ── Section locking ───────────────────────────────────────────────────────────

async def test_update_application_section(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    app = await _make_application(db, test_org, g, stage="writing")

    section = ApplicationSection(
        id=uuid.uuid4(),
        application_id=app.id,
        title="Project Narrative",
        content="",
        word_limit=500,
        sort_order=1,
        is_required=False,
        status="not_started",
    )
    db.add(section)
    await db.flush()

    res = await client.patch(
        f"/v1/applications/{app.id}/sections/{section.id}",
        json={"content": "Updated narrative content here."},
        headers=auth_headers,
    )
    assert res.status_code in (200, 204)


async def test_locked_section_cannot_be_edited(
    client: AsyncClient, auth_headers: dict, db: AsyncSession, test_org: Organization, test_user: User
):
    funder = await _make_funder(db)
    g = await _make_grant(db, funder)
    app = await _make_application(db, test_org, g, stage="internal_review")

    # Create a second user so locked_by satisfies the FK constraint
    other_user = User(
        id=uuid.uuid4(),
        org_id=test_org.id,
        email=f"other-{uuid.uuid4().hex[:8]}@testsymphony.test",
        password_hash=test_user.password_hash,
        first_name="Other",
        last_name="User",
        role="staff",
        is_active=True,
    )
    db.add(other_user)
    await db.flush()

    locked_section = ApplicationSection(
        id=uuid.uuid4(),
        application_id=app.id,
        title="Budget",
        content="$25,000",
        sort_order=2,
        is_required=False,
        status="not_started",
        locked_by=other_user.id,  # Locked by another real user
    )
    db.add(locked_section)
    await db.flush()

    res = await client.patch(
        f"/v1/applications/{app.id}/sections/{locked_section.id}",
        json={"content": "Trying to edit locked section"},
        headers=auth_headers,
    )
    assert res.status_code in (400, 403, 409)
