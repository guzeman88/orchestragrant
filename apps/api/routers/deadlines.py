from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from dependencies import CurrentUser
from models import Deadline
from schemas import DeadlineCreate, DeadlineRead

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/deadlines", tags=["deadlines"])


@router.get("", response_model=list[DeadlineRead])
async def list_deadlines(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    upcoming_only: bool = Query(False),
):
    from datetime import datetime, timezone
    stmt = select(Deadline).where(Deadline.org_id == current_user.org_id)
    if upcoming_only:
        stmt = stmt.where(Deadline.deadline_at > datetime.now(timezone.utc), Deadline.is_completed == False)
    stmt = stmt.order_by(Deadline.deadline_at.asc())
    result = await db.execute(stmt)
    return [DeadlineRead.model_validate(d) for d in result.scalars().all()]


@router.post("", response_model=DeadlineRead, status_code=status.HTTP_201_CREATED)
async def create_deadline(
    body: DeadlineCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    deadline = Deadline(org_id=current_user.org_id, **body.model_dump())
    db.add(deadline)
    await db.flush()
    return DeadlineRead.model_validate(deadline)


@router.patch("/{deadline_id}/complete", response_model=DeadlineRead)
async def mark_complete(
    deadline_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone
    result = await db.execute(
        select(Deadline).where(Deadline.id == deadline_id, Deadline.org_id == current_user.org_id)
    )
    deadline = result.scalar_one_or_none()
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    deadline.is_completed = True
    deadline.completed_at = datetime.now(timezone.utc)
    await db.flush()
    return DeadlineRead.model_validate(deadline)


@router.delete("/{deadline_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deadline(
    deadline_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Deadline).where(Deadline.id == deadline_id, Deadline.org_id == current_user.org_id)
    )
    deadline = result.scalar_one_or_none()
    if not deadline:
        raise HTTPException(status_code=404, detail="Deadline not found")
    await db.delete(deadline)
    await db.flush()
