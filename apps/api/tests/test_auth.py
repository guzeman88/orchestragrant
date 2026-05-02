"""Auth endpoint tests: login, lockout, MFA, refresh token rotation, logout."""
from __future__ import annotations

import secrets
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from models import Organization, User
from services.auth_service import hash_password


pytestmark = pytest.mark.asyncio


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _register_user(db: AsyncSession, org: Organization, password: str = "Password123!") -> User:
    user = User(
        id=uuid.uuid4(),
        org_id=org.id,
        email=f"auth-{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hash_password(password),
        first_name="Auth",
        last_name="User",
        role="director",
        is_active=True,
    )
    db.add(user)
    await db.flush()
    return user


# ── Login ─────────────────────────────────────────────────────────────────────

async def test_login_success(client: AsyncClient, db: AsyncSession, test_org: Organization):
    pw = "GoodPassword1!"
    user = await _register_user(db, test_org, password=pw)

    res = await client.post("/v1/auth/login", json={"email": user.email, "password": pw})
    assert res.status_code == 200
    body = res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert isinstance(body["expires_in"], int)


async def test_login_wrong_password(client: AsyncClient, db: AsyncSession, test_org: Organization):
    user = await _register_user(db, test_org)
    res = await client.post("/v1/auth/login", json={"email": user.email, "password": "WrongPass1!"})
    assert res.status_code == 401


async def test_login_nonexistent_user(client: AsyncClient):
    res = await client.post("/v1/auth/login", json={"email": "nobody@nowhere.test", "password": "x"})
    assert res.status_code == 401


async def test_login_inactive_user(client: AsyncClient, db: AsyncSession, test_org: Organization):
    user = await _register_user(db, test_org)
    user.is_active = False
    await db.flush()

    res = await client.post("/v1/auth/login", json={"email": user.email, "password": "Password123!"})
    assert res.status_code == 401


# ── Account lockout ───────────────────────────────────────────────────────────

async def test_account_lockout_after_5_failures(
    client: AsyncClient, db: AsyncSession, test_org: Organization
):
    user = await _register_user(db, test_org)

    for _ in range(5):
        await client.post("/v1/auth/login", json={"email": user.email, "password": "BadPass!"})

    # 6th attempt should be locked
    res = await client.post("/v1/auth/login", json={"email": user.email, "password": "BadPass!"})
    assert res.status_code == 429


# ── Token refresh ─────────────────────────────────────────────────────────────

async def test_refresh_token_rotation(client: AsyncClient, db: AsyncSession, test_org: Organization):
    pw = "Refresh123!"
    user = await _register_user(db, test_org, password=pw)

    login_res = await client.post("/v1/auth/login", json={"email": user.email, "password": pw})
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    refresh_res = await client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_res.status_code == 200
    body = refresh_res.json()
    assert "access_token" in body
    assert "refresh_token" in body
    # New refresh token must differ from the old one
    assert body["refresh_token"] != refresh_token


async def test_refresh_token_reuse_rejected(
    client: AsyncClient, db: AsyncSession, test_org: Organization
):
    pw = "Reuse123!"
    user = await _register_user(db, test_org, password=pw)

    login_res = await client.post("/v1/auth/login", json={"email": user.email, "password": pw})
    old_refresh = login_res.json()["refresh_token"]

    # Use the token once
    await client.post("/v1/auth/refresh", json={"refresh_token": old_refresh})

    # Attempt to reuse — must be rejected
    reuse_res = await client.post("/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_res.status_code == 401


async def test_invalid_refresh_token_rejected(client: AsyncClient):
    res = await client.post("/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})
    assert res.status_code == 401


# ── Logout ────────────────────────────────────────────────────────────────────

async def test_logout(client: AsyncClient, db: AsyncSession, test_org: Organization):
    pw = "Logout123!"
    user = await _register_user(db, test_org, password=pw)

    login_res = await client.post("/v1/auth/login", json={"email": user.email, "password": pw})
    access = login_res.json()["access_token"]
    refresh = login_res.json()["refresh_token"]

    logout_res = await client.post(
        "/v1/auth/logout",
        json={"refresh_token": refresh},
        headers={"Authorization": f"Bearer {access}"},
    )
    assert logout_res.status_code in (200, 204)

    # After logout, refresh token must be invalid
    retry_res = await client.post("/v1/auth/refresh", json={"refresh_token": refresh})
    assert retry_res.status_code == 401


# ── /me endpoint ──────────────────────────────────────────────────────────────

async def test_get_me_authenticated(client: AsyncClient, auth_headers: dict):
    res = await client.get("/v1/users/me", headers=auth_headers)
    assert res.status_code == 200
    assert "email" in res.json()


async def test_get_me_unauthenticated(client: AsyncClient):
    res = await client.get("/v1/users/me")
    assert res.status_code == 401
