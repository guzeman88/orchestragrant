from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from dependencies import CurrentUser, DirectorOrAbove
from models import Grant, Funder, GrantWatchlistItem
from schemas import GrantRead, GrantSearch, PaginatedGrants, FunderRead

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/grants", tags=["grants"])


@router.get("", response_model=PaginatedGrants)
async def list_grants(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    query: str | None = Query(None),
    search: str | None = Query(None),  # alias for query
    type: str | None = Query(None),
    grant_type: str | None = Query(None),  # alias for type
    funder_type: str | None = Query(None),
    min_amount: float | None = Query(None, ge=0),
    max_amount: float | None = Query(None, ge=0),
    amount_max: float | None = Query(None, ge=0),  # alias for max_amount
    amount_min: float | None = Query(None, ge=0),  # alias for min_amount
    arts_specific: bool | None = Query(None),
    is_active: bool = Query(True),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    sort_by: str = Query("relevance"),
    sort_order: str = Query("desc"),
):
    # Resolve aliases
    effective_query = query or search
    effective_type = type or grant_type
    effective_max = max_amount if max_amount is not None else amount_max
    effective_min = min_amount if min_amount is not None else amount_min

    stmt = (
        select(Grant)
        .options(selectinload(Grant.funder))
        .where(Grant.is_active == is_active)
    )

    if effective_query:
        fts = text("to_tsvector('english', coalesce(grants.grants.title,'') || ' ' || coalesce(grants.grants.description,'')) @@ plainto_tsquery('english', :q)")
        stmt = stmt.where(fts.bindparams(q=effective_query))

    if effective_type:
        stmt = stmt.where(Grant.type == effective_type)

    if funder_type:
        stmt = stmt.join(Grant.funder).where(Funder.type == funder_type)
    else:
        stmt = stmt.join(Grant.funder)

    if arts_specific is not None:
        stmt = stmt.where(Funder.arts_specific == arts_specific)

    if effective_min is not None:
        stmt = stmt.where(
            or_(Grant.typical_amount >= effective_min, Grant.max_amount >= effective_min)
        )
    if effective_max is not None:
        stmt = stmt.where(
            or_(Grant.typical_amount <= effective_max, Grant.min_amount <= effective_max)
        )

    # Count
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    # Sort
    if sort_by == "deadline":
        order_col = Grant.deadline.asc() if sort_order == "asc" else Grant.deadline.desc()
    elif sort_by == "amount":
        order_col = Grant.typical_amount.asc() if sort_order == "asc" else Grant.typical_amount.desc()
    else:
        order_col = Grant.updated_at.desc()

    stmt = stmt.order_by(order_col).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    grants = result.scalars().all()

    return PaginatedGrants(
        items=[GrantRead.model_validate(g) for g in grants],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.get("/{grant_id}", response_model=GrantRead)
async def get_grant(
    grant_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Grant).options(selectinload(Grant.funder)).where(Grant.id == grant_id)
    )
    grant = result.scalar_one_or_none()
    if not grant:
        raise HTTPException(status_code=404, detail="Grant not found")
    return GrantRead.model_validate(grant)


@router.post("/{grant_id}/watchlist", status_code=status.HTTP_201_CREATED)
@router.post("/{grant_id}/watch", status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    grant_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Verify grant exists
    result = await db.execute(select(Grant).where(Grant.id == grant_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Grant not found")

    # Idempotent
    existing = await db.execute(
        select(GrantWatchlistItem).where(
            GrantWatchlistItem.org_id == current_user.org_id,
            GrantWatchlistItem.grant_id == grant_id,
        )
    )
    if existing.scalar_one_or_none():
        return {"message": "Already on watchlist"}

    item = GrantWatchlistItem(
        org_id=current_user.org_id,
        grant_id=grant_id,
        added_by=current_user.id,
    )
    db.add(item)
    await db.flush()
    return {"message": "Added to watchlist"}


@router.delete("/{grant_id}/watchlist", status_code=status.HTTP_204_NO_CONTENT)
@router.delete("/{grant_id}/watch", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    grant_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GrantWatchlistItem).where(
            GrantWatchlistItem.org_id == current_user.org_id,
            GrantWatchlistItem.grant_id == grant_id,
        )
    )
    item = result.scalar_one_or_none()
    if item:
        await db.delete(item)
        await db.flush()


@router.get("/watchlist/me", response_model=list[GrantRead])
async def get_my_watchlist(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Grant)
        .options(selectinload(Grant.funder))
        .join(GrantWatchlistItem, GrantWatchlistItem.grant_id == Grant.id)
        .where(GrantWatchlistItem.org_id == current_user.org_id)
        .order_by(GrantWatchlistItem.created_at.desc())
    )
    grants = result.scalars().all()
    return [GrantRead.model_validate(g) for g in grants]
