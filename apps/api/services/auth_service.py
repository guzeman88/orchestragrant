from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import pyotp
import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config import settings
from models import User, RefreshToken

logger = structlog.get_logger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, org_id: str, role: str) -> tuple[str, int]:
    expires = _utcnow() + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "org_id": org_id,
        "role": role,
        "exp": expires,
        "iat": _utcnow(),
        "type": "access",
    }
    token = jwt.encode(payload, settings.JWT_PRIVATE_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_PUBLIC_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp", "org_id", "role"]},
    )


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def create_refresh_token(
    db: AsyncSession,
    user_id: UUID,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
) -> str:
    raw_token = secrets.token_urlsafe(64)
    token_hash = _hash_token(raw_token)
    expires = _utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(rt)
    await db.flush()
    return raw_token


async def verify_refresh_token(db: AsyncSession, raw_token: str) -> Optional[User]:
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken)
        .options(selectinload(RefreshToken.user))
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
            RefreshToken.expires_at > _utcnow(),
        )
    )
    rt = result.scalar_one_or_none()
    if not rt:
        return None
    # Revoke after use (rotation)
    rt.revoked_at = _utcnow()
    await db.flush()
    return rt.user


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> bool:
    """Revoke a refresh token by raw value. Returns True if found and revoked."""
    token_hash = _hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked_at.is_(None),
        )
    )
    rt = result.scalar_one_or_none()
    if not rt:
        return False
    rt.revoked_at = _utcnow()
    await db.flush()
    return True


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def record_login_success(db: AsyncSession, user: User) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = _utcnow()
    await db.flush()


async def record_login_failure(db: AsyncSession, user: User) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= settings.RATE_LIMIT_LOGIN_LOCKOUT_ATTEMPTS:
        user.locked_until = _utcnow() + timedelta(minutes=settings.RATE_LIMIT_LOGIN_LOCKOUT_MINUTES)
        logger.warning("Account locked", user_id=str(user.id), email=user.email)
    await db.flush()


def is_account_locked(user: User) -> bool:
    if user.locked_until and user.locked_until > _utcnow():
        return True
    return False


def generate_totp_secret() -> str:
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name="OrchestraGrant")


def verify_totp(secret: str, code: str) -> bool:
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
