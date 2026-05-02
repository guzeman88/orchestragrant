from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import CurrentUser, DirectorOrAbove
from models import User
from schemas import UserRead, UserUpdate, InviteUserRequest
from services.auth_service import hash_password
import secrets

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUser):
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    await db.flush()
    return UserRead.model_validate(current_user)


@router.get("", response_model=list[UserRead])
async def list_users(
    current_user: DirectorOrAbove,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.org_id == current_user.org_id, User.is_active == True)
        .order_by(User.first_name)
    )
    return [UserRead.model_validate(u) for u in result.scalars().all()]


@router.post("/invite", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def invite_user(
    body: InviteUserRequest,
    current_user: DirectorOrAbove,
    db: AsyncSession = Depends(get_db),
):
    # Check email not already in use within org
    existing = await db.execute(select(User).where(User.email == body.email.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="A user with this email already exists")

    # Create user with a temporary random password (they must reset via email)
    temp_password = secrets.token_urlsafe(24)
    user = User(
        org_id=current_user.org_id,
        email=body.email.lower(),
        password_hash=hash_password(temp_password),
        first_name=body.first_name,
        last_name=body.last_name,
        role=body.role,
        invited_by=current_user.id,
    )
    db.add(user)
    await db.flush()

    # Queue invite email via Celery
    from tasks.email_tasks import send_invite_email
    from config import settings
    base_url = getattr(settings, "APP_BASE_URL", "https://app.orchestragrant.com")
    invite_url = f"{base_url}/login?invite=1"
    send_invite_email.delay(str(user.id), invite_url, temp_password)

    logger.info("User invited", invitee_email=body.email, invited_by=str(current_user.id))
    return UserRead.model_validate(user)


@router.patch("/{user_id}/deactivate", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: UUID,
    current_user: DirectorOrAbove,
    db: AsyncSession = Depends(get_db),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
    result = await db.execute(
        select(User).where(User.id == user_id, User.org_id == current_user.org_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_active = False
    await db.flush()
