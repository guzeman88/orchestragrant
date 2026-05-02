from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database import get_db
from dependencies import CurrentUser, DirectorOrAbove
from models import Application, ApplicationSection, Deadline, Grant, Funder
from schemas import (
    ApplicationCreate, ApplicationRead, ApplicationUpdate,
    ApplicationSectionRead, SectionUpdate,
    StageTransitionRequest, PaginatedApplications,
    DeadlineCreate, DeadlineRead,
)

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/applications", tags=["applications"])

VALID_STAGES = {
    "prospecting", "qualifying", "writing", "internal_review",
    "director_review", "board_approval", "ready_to_submit", "submitted",
    "under_review", "awarded", "declined", "withdrawn",
}

# Allowed forward/back transitions (adjacency list)
STAGE_TRANSITIONS: dict[str, set[str]] = {
    "prospecting": {"qualifying", "withdrawn"},
    "qualifying": {"writing", "prospecting", "withdrawn"},
    "writing": {"internal_review", "qualifying", "withdrawn"},
    "internal_review": {"director_review", "writing", "withdrawn"},
    "director_review": {"board_approval", "internal_review", "writing", "withdrawn"},
    "board_approval": {"ready_to_submit", "director_review", "withdrawn"},
    "ready_to_submit": {"submitted", "board_approval", "withdrawn"},
    "submitted": {"under_review", "withdrawn"},
    "under_review": {"awarded", "declined"},
    "awarded": set(),
    "declined": set(),
    "withdrawn": set(),
}


@router.get("", response_model=PaginatedApplications)
async def list_applications(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    stage: str | None = Query(None),
    assigned_to: UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
):
    stmt = (
        select(Application)
        .options(selectinload(Application.grant).selectinload(Grant.funder))
        .options(selectinload(Application.assigned_user))
        .where(Application.org_id == current_user.org_id)
    )
    if stage:
        stmt = stmt.where(Application.stage == stage)
    if assigned_to:
        stmt = stmt.where(Application.assigned_to == assigned_to)

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()
    stmt = stmt.order_by(Application.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    apps = result.scalars().all()

    return PaginatedApplications(
        items=[ApplicationRead.model_validate(a) for a in apps],
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post("", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
async def create_application(
    body: ApplicationCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    app = Application(
        org_id=current_user.org_id,
        **body.model_dump(exclude_unset=True),
    )
    app.stage_history = []
    db.add(app)
    await db.flush()

    # Auto-create deadline if provided
    if body.submission_deadline:
        deadline = Deadline(
            org_id=current_user.org_id,
            application_id=app.id,
            grant_id=body.grant_id,
            title=f"Submit: {body.title}",
            deadline_at=body.submission_deadline,
            type="application",
        )
        db.add(deadline)
        await db.flush()

    logger.info("Application created", app_id=str(app.id), org_id=str(current_user.org_id))
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.grant).selectinload(Grant.funder))
        .options(selectinload(Application.assigned_user))
        .where(Application.id == app.id)
    )
    app = result.scalar_one()
    return ApplicationRead.model_validate(app)


@router.get("/{app_id}", response_model=ApplicationRead)
async def get_application(
    app_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.grant).selectinload(Grant.funder))
        .options(selectinload(Application.assigned_user))
        .options(selectinload(Application.sections))
        .where(Application.id == app_id, Application.org_id == current_user.org_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return ApplicationRead.model_validate(app)


@router.patch("/{app_id}", response_model=ApplicationRead)
async def update_application(
    app_id: UUID,
    body: ApplicationUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application)
        .options(selectinload(Application.grant).selectinload(Grant.funder))
        .options(selectinload(Application.assigned_user))
        .where(Application.id == app_id, Application.org_id == current_user.org_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Submitted applications are immutable
    if app.stage == "submitted":
        raise HTTPException(status_code=400, detail="Submitted applications cannot be edited")

    updates = body.model_dump(exclude_unset=True)

    # Validate stage transition if stage is being changed
    if "stage" in updates:
        new_stage = updates.pop("stage")
        if new_stage not in VALID_STAGES:
            raise HTTPException(status_code=400, detail=f"Invalid stage: {new_stage}")
        allowed = STAGE_TRANSITIONS.get(app.stage, set())
        if new_stage not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from '{app.stage}' to '{new_stage}'",
            )
        app.stage = new_stage

    for field, value in updates.items():
        setattr(app, field, value)
    await db.flush()
    # Re-query with relationships to avoid lazy-load errors
    result2 = await db.execute(
        select(Application)
        .options(selectinload(Application.grant).selectinload(Grant.funder))
        .options(selectinload(Application.assigned_user))
        .where(Application.id == app_id)
    )
    return ApplicationRead.model_validate(result2.scalar_one())


@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_application(
    app_id: UUID,
    current_user: DirectorOrAbove,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.org_id == current_user.org_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    await db.delete(app)
    await db.flush()


@router.post("/{app_id}/stage", response_model=ApplicationRead)
async def transition_stage(
    app_id: UUID,
    body: StageTransitionRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    if body.new_stage not in VALID_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage: {body.new_stage}")

    result = await db.execute(
        select(Application).where(Application.id == app_id, Application.org_id == current_user.org_id)
    )
    app = result.scalar_one_or_none()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    allowed = STAGE_TRANSITIONS.get(app.stage, set())
    if body.new_stage not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{app.stage}' to '{body.new_stage}'",
        )

    from datetime import datetime, timezone
    history_entry = {
        "from_stage": app.stage,
        "to_stage": body.new_stage,
        "changed_by": str(current_user.id),
        "changed_at": datetime.now(timezone.utc).isoformat(),
        "note": body.note,
    }
    app.stage_history = [*(app.stage_history or []), history_entry]
    app.stage = body.new_stage
    await db.flush()

    # Auto-create default sections when entering writing stage
    if body.new_stage == "writing":
        existing = await db.execute(
            select(ApplicationSection).where(ApplicationSection.application_id == app_id)
        )
        if not existing.scalars().all():
            DEFAULT_SECTIONS = [
                ("Project Narrative", 1000, True, 1),
                ("Goals & Objectives", 500, True, 2),
                ("Budget Narrative", 750, True, 3),
                ("Evaluation Plan", 500, False, 4),
                ("Organizational Capacity", 500, False, 5),
            ]
            for title, word_limit, is_required, sort_order in DEFAULT_SECTIONS:
                section = ApplicationSection(
                    application_id=app_id,
                    title=title,
                    word_limit=word_limit,
                    is_required=is_required,
                    sort_order=sort_order,
                    status="not_started",
                )
                db.add(section)
            await db.flush()

    logger.info("Stage transition", app_id=str(app_id), from_stage=history_entry["from_stage"], to_stage=body.new_stage)
    result2 = await db.execute(
        select(Application)
        .options(selectinload(Application.grant).selectinload(Grant.funder))
        .options(selectinload(Application.assigned_user))
        .where(Application.id == app_id)
    )
    return ApplicationRead.model_validate(result2.scalar_one())


# ─── Sections ─────────────────────────────────────────────────────────────────

@router.get("/{app_id}/sections", response_model=list[ApplicationSectionRead])
async def list_sections(
    app_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    # Verify app belongs to org
    app_result = await db.execute(
        select(Application).where(Application.id == app_id, Application.org_id == current_user.org_id)
    )
    if not app_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Application not found")

    result = await db.execute(
        select(ApplicationSection)
        .where(ApplicationSection.application_id == app_id)
        .order_by(ApplicationSection.sort_order)
    )
    return [ApplicationSectionRead.model_validate(s) for s in result.scalars().all()]


@router.patch("/{app_id}/sections/{section_id}", response_model=ApplicationSectionRead)
async def update_section(
    app_id: UUID,
    section_id: UUID,
    body: SectionUpdate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApplicationSection)
        .join(ApplicationSection.application)
        .where(
            ApplicationSection.id == section_id,
            ApplicationSection.application_id == app_id,
            Application.org_id == current_user.org_id,
        )
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if section.locked_by and section.locked_by != current_user.id:
        raise HTTPException(status_code=409, detail="Section is locked by another user")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(section, field, value)
    section.last_edited_by = current_user.id
    await db.flush()
    await db.refresh(section)
    return ApplicationSectionRead.model_validate(section)


@router.post("/{app_id}/sections/{section_id}/lock", response_model=ApplicationSectionRead)
async def lock_section(
    app_id: UUID,
    section_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime, timezone

    result = await db.execute(
        select(ApplicationSection)
        .join(ApplicationSection.application)
        .where(
            ApplicationSection.id == section_id,
            ApplicationSection.application_id == app_id,
            Application.org_id == current_user.org_id,
        )
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if section.locked_by and section.locked_by != current_user.id:
        raise HTTPException(status_code=409, detail="Section is already locked")

    section.locked_by = current_user.id
    section.locked_at = datetime.now(timezone.utc)
    await db.flush()
    return ApplicationSectionRead.model_validate(section)


@router.delete("/{app_id}/sections/{section_id}/lock", status_code=status.HTTP_204_NO_CONTENT)
async def unlock_section(
    app_id: UUID,
    section_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApplicationSection)
        .join(ApplicationSection.application)
        .where(
            ApplicationSection.id == section_id,
            ApplicationSection.application_id == app_id,
            Application.org_id == current_user.org_id,
        )
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if section.locked_by and section.locked_by != current_user.id:
        raise HTTPException(status_code=403, detail="Cannot unlock another user's lock")

    section.locked_by = None
    section.locked_at = None
    await db.flush()


@router.post("/{app_id}/sections/{section_id}/generate", response_model=ApplicationSectionRead)
async def generate_section_content(
    app_id: UUID,
    section_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Generate template content for a section using org profile data."""
    from models import Organization, OrgProfile

    result = await db.execute(
        select(ApplicationSection)
        .join(ApplicationSection.application)
        .where(
            ApplicationSection.id == section_id,
            ApplicationSection.application_id == app_id,
            Application.org_id == current_user.org_id,
        )
    )
    section = result.scalar_one_or_none()
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    if section.locked_by and section.locked_by != current_user.id:
        raise HTTPException(status_code=409, detail="Section is locked by another user")

    # Fetch org + profile for context
    org_result = await db.execute(select(Organization).where(Organization.id == current_user.org_id))
    org = org_result.scalar_one_or_none()

    profile_result = await db.execute(
        select(OrgProfile).where(OrgProfile.org_id == current_user.org_id)
    )
    profile = profile_result.scalar_one_or_none()

    org_name = org.name if org else "Our organization"
    mission = (profile.mission if profile and profile.mission else None)
    programs = (profile.programs_description if profile and profile.programs_description else None)
    impact = (profile.community_impact_statement if profile and profile.community_impact_statement else None)

    title_lower = (section.title or "").lower()

    if any(k in title_lower for k in ["mission", "purpose", "about", "overview"]):
        content = mission or (
            f"{org_name} is a performing arts organization dedicated to artistic excellence and community enrichment. "
            f"[Expand on your mission here.]"
        )
    elif any(k in title_lower for k in ["project", "program", "activit"]):
        content = programs or (
            f"The proposed project will [describe project activities]. "
            f"This initiative builds on {org_name}'s expertise in [area]. "
            f"[Describe timeline, key activities, and deliverables.]"
        )
    elif any(k in title_lower for k in ["impact", "community", "audience", "outcome"]):
        content = impact or (
            f"{org_name} serves [describe community] through high-quality artistic programming. "
            f"This project will directly impact [number] community members by [describe impact]. "
            f"[Provide specific outcome metrics here.]"
        )
    elif any(k in title_lower for k in ["budget", "financial", "cost", "fund"]):
        content = (
            f"Total project budget: $[AMOUNT]\n"
            f"Requested grant funding: $[GRANT_AMOUNT]\n\n"
            f"Budget breakdown:\n"
            f"- Personnel: $[AMOUNT] ([X]%)\n"
            f"- Materials & supplies: $[AMOUNT] ([X]%)\n"
            f"- Marketing & outreach: $[AMOUNT] ([X]%)\n"
            f"- Administrative overhead: $[AMOUNT] ([X]%)\n\n"
            f"[Add notes on matching funds, in-kind contributions, or other revenue sources.]"
        )
    elif any(k in title_lower for k in ["evaluat", "measur", "success", "metric"]):
        content = (
            f"{org_name} will evaluate this project's success using the following measures:\n\n"
            f"1. [Quantitative metric — e.g., number of performances, attendance]\n"
            f"2. [Audience/participant satisfaction — e.g., post-event surveys]\n"
            f"3. [Artistic outcome — e.g., world premieres, new commissions]\n"
            f"4. [Community reach — e.g., school partnerships, free tickets distributed]\n\n"
            f"Data will be collected via [methods] and reported to the funder [timeline]."
        )
    elif any(k in title_lower for k in ["qualif", "capacit", "experience", "track"]):
        content = (
            f"{org_name} has [X years] of experience delivering high-quality arts programming. "
            f"Our team of [X] professional musicians and [X] administrative staff has successfully "
            f"managed projects of similar scope, including [brief example]. "
            f"[Highlight relevant past accomplishments and organizational strengths.]"
        )
    else:
        content = (
            f"[Draft content for '{section.title}']\n\n"
            f"[Please customize this section with specific details about {org_name}'s plans, "
            f"qualifications, and goals as they relate to this grant opportunity.]"
        )

    section.content = content
    section.status = "in_progress"
    section.last_edited_by = current_user.id
    await db.flush()
    await db.refresh(section)
    return ApplicationSectionRead.model_validate(section)
