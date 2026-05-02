from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Organization, OrgProfile


async def calculate_completeness(db: AsyncSession, org: Organization) -> int:
    """Return a 0-100 completeness score for the org profile."""
    score = 0

    # Basic org fields (50 points)
    fields_50 = [
        org.name, org.legal_name, org.ein, org.primary_email,
        org.website, org.phone, org.address_city, org.address_state,
        org.founded_year, org.budget_size,
    ]
    score += sum(5 for f in fields_50 if f)

    # Profile fields (50 points)
    result = await db.execute(select(OrgProfile).where(OrgProfile.org_id == org.id))
    profile = result.scalar_one_or_none()
    if profile:
        profile_fields = [
            profile.mission, profile.vision, profile.programs_description,
            profile.geographic_scope, profile.primary_artistic_focus,
            profile.community_impact_statement, profile.diversity_statement,
            profile.performances_per_year, profile.audience_size, profile.member_musicians,
        ]
        score += sum(5 for f in profile_fields if f)

    return min(score, 100)
