from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import CurrentUser, DirectorOrAbove
from models import Organization, OrgProfile
from schemas import OrgRead, OrgUpdate, OrgProfileRead, OrgProfileUpdate
from services.completeness_service import calculate_completeness

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("/me", response_model=OrgRead)
async def get_my_org(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return OrgRead.model_validate(org)


@router.patch("/me", response_model=OrgRead)
async def update_my_org(
    body: OrgUpdate,
    current_user: DirectorOrAbove,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(org, field, value)

    org.profile_completeness_score = await calculate_completeness(db, org)
    await db.flush()
    logger.info("Org updated", org_id=str(org.id), fields=list(update_data.keys()))
    result2 = await db.execute(select(Organization).where(Organization.id == org.id))
    org = result2.scalar_one()
    return OrgRead.model_validate(org)


@router.get("/me/profile", response_model=OrgProfileRead)
async def get_org_profile(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(OrgProfile).where(OrgProfile.org_id == current_user.org_id))
    profile = result.scalar_one_or_none()
    if not profile:
        # Auto-create profile if it doesn't exist yet
        profile = OrgProfile(org_id=current_user.org_id)
        db.add(profile)
        await db.flush()
        result = await db.execute(select(OrgProfile).where(OrgProfile.org_id == current_user.org_id))
        profile = result.scalar_one()
    return OrgProfileRead.model_validate(profile)


@router.patch("/me/profile", response_model=OrgProfileRead)
async def update_org_profile(
    body: OrgProfileUpdate,
    current_user: DirectorOrAbove,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(OrgProfile).where(OrgProfile.org_id == current_user.org_id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = OrgProfile(org_id=current_user.org_id)
        db.add(profile)
        await db.flush()

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    await db.flush()

    # Recalculate completeness
    org_result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_result.scalar_one()
    org.profile_completeness_score = await calculate_completeness(db, org)
    await db.flush()

    result2 = await db.execute(select(OrgProfile).where(OrgProfile.org_id == current_user.org_id))
    profile = result2.scalar_one()
    return OrgProfileRead.model_validate(profile)
