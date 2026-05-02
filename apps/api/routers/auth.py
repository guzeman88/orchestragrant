from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import CurrentUser
from schemas import (
    LoginRequest, LoginResponse, RefreshRequest, RefreshResponse,
    MfaSetupResponse, MfaVerifyRequest, UserRead, OrgRead, LogoutRequest,
)
from services import auth_service
from models import Organization
from sqlalchemy import select

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.get_user_by_email(db, body.email)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account is disabled")

    if auth_service.is_account_locked(user):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Account temporarily locked due to too many failed attempts",
        )

    if not auth_service.verify_password(body.password, user.password_hash):
        await auth_service.record_login_failure(db, user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if user.is_mfa_enabled:
        if not body.totp_code:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="MFA code required")
        if not auth_service.verify_totp(user.mfa_secret, body.totp_code):
            await auth_service.record_login_failure(db, user)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid MFA code")

    await auth_service.record_login_success(db, user)
    await db.refresh(user)  # re-load server-updated columns (updated_at, etc.)

    access_token, expires_in = auth_service.create_access_token(
        user_id=str(user.id),
        org_id=str(user.org_id),
        role=user.role,
    )
    refresh_token = await auth_service.create_refresh_token(
        db,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    org_result = await db.execute(select(Organization).where(Organization.id == user.org_id))
    org = org_result.scalar_one()

    logger.info("User logged in", user_id=str(user.id), org_id=str(user.org_id))
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        user=UserRead.model_validate(user),
        org=OrgRead.model_validate(org),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = await auth_service.verify_refresh_token(db, body.refresh_token)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    access_token, expires_in = auth_service.create_access_token(
        user_id=str(user.id),
        org_id=str(user.org_id),
        role=user.role,
    )
    new_refresh_token = await auth_service.create_refresh_token(
        db,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return RefreshResponse(access_token=access_token, refresh_token=new_refresh_token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if body.refresh_token:
        await auth_service.revoke_refresh_token(db, body.refresh_token)
    logger.info("User logged out", user_id=str(current_user.id))


@router.post("/mfa/setup", response_model=MfaSetupResponse)
async def setup_mfa(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    if current_user.is_mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA already enabled")
    secret = auth_service.generate_totp_secret()
    uri = auth_service.get_totp_uri(secret, current_user.email)
    # Temporarily store secret (not enabled until verified)
    current_user.mfa_secret = secret
    await db.flush()
    return MfaSetupResponse(secret=secret, qr_data_uri=uri)


@router.post("/mfa/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_mfa(
    body: MfaVerifyRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="MFA setup not initiated")
    if not auth_service.verify_totp(current_user.mfa_secret, body.totp_code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    current_user.is_mfa_enabled = True
    await db.flush()


@router.delete("/mfa", status_code=status.HTTP_204_NO_CONTENT)
async def disable_mfa(
    body: MfaVerifyRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if not current_user.is_mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA not enabled")
    if not auth_service.verify_totp(current_user.mfa_secret, body.totp_code):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")
    current_user.is_mfa_enabled = False
    current_user.mfa_secret = None
    await db.flush()
