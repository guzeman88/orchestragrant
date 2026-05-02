"""Pytest fixtures shared across all API test modules."""
from __future__ import annotations

import asyncio
import secrets
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
import sqlalchemy as sa
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from config import settings
from database import Base
from main import app
from models import Organization, User
from services.auth_service import hash_password, create_access_token

# ── Test DB ───────────────────────────────────────────────────────────────────

# Override DB URL to a test database
# Replace only the database name (path component), not the username
from urllib.parse import urlparse, urlunparse
_parsed = urlparse(settings.DATABASE_URL)
TEST_DATABASE_URL = urlunparse(_parsed._replace(path="/orchestragrant_test")) \
    if settings.DATABASE_URL else settings.DATABASE_URL


@pytest.fixture(scope="session")
def event_loop_policy():
    """Use the default asyncio event loop policy for the session."""
    import asyncio
    return asyncio.DefaultEventLoopPolicy()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with eng.begin() as conn:
        # Create schemas and extensions first
        await conn.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        for schema in ("auth", "grants", "applications", "awards", "ai", "discovery"):
            await conn.execute(sa.text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    # Drop all tables in correct schema order
    async with eng.begin() as conn:
        for schema in ("ai", "awards", "applications", "grants", "auth"):
            await conn.execute(sa.text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
        for tbl in ("deadlines", "org_documents", "board_members", "org_profiles", "organizations"):
            await conn.execute(sa.text(f"DROP TABLE IF EXISTS {tbl} CASCADE"))
    await eng.dispose()


# Tables to truncate between tests (in safe order)
_TRUNCATE_TABLES = [
    "ai.narrative_atoms",
    "awards.awards",
    "applications.application_sections",
    "applications.applications",
    "grants.grant_watchlist",
    "grants.grants",
    "grants.funders",
    "auth.refresh_tokens",
    "auth.users",
    "deadlines",
    "org_documents",
    "board_members",
    "org_profiles",
    "organizations",
]


@pytest_asyncio.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Fresh session per test, tables truncated after each test."""
    session_factory = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.rollback()
            # Truncate all test data
            async with engine.begin() as conn:
                tables = ", ".join(_TRUNCATE_TABLES)
                await conn.execute(sa.text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))


# ── Factories ─────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_org(db: AsyncSession) -> Organization:
    org = Organization(
        id=uuid.uuid4(),
        name="Test Symphony",
        legal_name="Test Symphony Orchestra Inc.",
        ein=f"99-{secrets.randbelow(9000000) + 1000000}",
        org_type="symphony",
        subscription_tier="professional",
        subscription_status="active",
        primary_email="admin@testsymphony.test",
        address_state="CA",
        is_onboarded=False,
        profile_completeness_score=0,
    )
    db.add(org)
    await db.flush()
    return org


@pytest_asyncio.fixture
async def test_user(db: AsyncSession, test_org: Organization) -> User:
    user = User(
        id=uuid.uuid4(),
        org_id=test_org.id,
        email=f"user-{uuid.uuid4().hex[:8]}@testsymphony.test",
        password_hash=hash_password("TestPassword123!"),
        first_name="Test",
        last_name="User",
        role="director",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def access_token(test_user: User, test_org: Organization) -> str:
    token, _ = create_access_token(
        user_id=str(test_user.id),
        org_id=str(test_org.id),
        role=test_user.role,
    )
    return token


@pytest_asyncio.fixture
async def auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


# ── HTTP client ───────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with DB session dependency override."""
    from database import get_db

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
