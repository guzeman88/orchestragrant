"""Seed the database with sample funders and grants for development."""
import asyncio
import uuid
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from config import settings
from models import Funder, Grant

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)


FUNDERS = [
    {
        "name": "National Endowment for the Arts",
        "type": "government_federal",
        "website": "https://www.arts.gov",
        "description": "The NEA is an independent federal agency that funds, promotes, and strengthens creative capacity across the nation.",
        "geographic_focus": ["national"],
        "arts_specific": True,
        "giving_range_min": 10000,
        "giving_range_max": 100000,
    },
    {
        "name": "Mellon Foundation",
        "type": "foundation",
        "website": "https://www.mellon.org",
        "description": "The Mellon Foundation believes that the arts and humanities are essential to human flourishing.",
        "geographic_focus": ["national"],
        "arts_specific": True,
        "giving_range_min": 50000,
        "giving_range_max": 500000,
    },
    {
        "name": "Sphinx Organization",
        "type": "foundation",
        "website": "https://www.sphinxmusic.org",
        "description": "Sphinx builds diversity in classical music through grants, competitions, and education programs.",
        "geographic_focus": ["national"],
        "arts_specific": True,
        "giving_range_min": 5000,
        "giving_range_max": 50000,
    },
    {
        "name": "American Symphony Orchestra League",
        "type": "foundation",
        "website": "https://www.americanorchestras.org",
        "description": "League of American Orchestras connects and strengthens America's orchestras.",
        "geographic_focus": ["national"],
        "arts_specific": True,
        "giving_range_min": 10000,
        "giving_range_max": 200000,
    },
    {
        "name": "Ford Foundation",
        "type": "foundation",
        "website": "https://www.fordfoundation.org",
        "description": "The Ford Foundation supports visionary leaders and organizations on the front lines of social change.",
        "geographic_focus": ["national", "international"],
        "arts_specific": False,
        "giving_range_min": 100000,
        "giving_range_max": 1000000,
    },
    {
        "name": "Doris Duke Charitable Foundation",
        "type": "foundation",
        "website": "https://www.ddcf.org",
        "description": "DDCF supports performing arts, environmental conservation, and medical research.",
        "geographic_focus": ["national"],
        "arts_specific": True,
        "giving_range_min": 50000,
        "giving_range_max": 300000,
    },
    {
        "name": "New York State Council on the Arts",
        "type": "government_state",
        "website": "https://www.arts.ny.gov",
        "description": "NYSCA advances equitable access to the arts through grant making and public programming across New York State.",
        "geographic_focus": ["New York"],
        "arts_specific": True,
        "giving_range_min": 5000,
        "giving_range_max": 150000,
    },
    {
        "name": "Pew Center for Arts & Heritage",
        "type": "foundation",
        "website": "https://www.pcah.us",
        "description": "Pew supports Philadelphia-area arts organizations through grants and cultural programs.",
        "geographic_focus": ["Pennsylvania", "Philadelphia"],
        "arts_specific": True,
        "giving_range_min": 25000,
        "giving_range_max": 250000,
    },
]

# (funder_index, title, type, min, max, deadline_days, description, tagline)
GRANTS = [
    (0, "Grants for Arts Projects", "project", 10000, 100000, 120,
     "NEA Grants for Arts Projects support the creation of art that meets the highest standards of excellence, engages the public, and reflects the breadth of America's creativity.",
     "Support for excellence in the arts"),
    (0, "Challenge America", "general_operating", 10000, 10000, 180,
     "Challenge America grants support projects in areas of the country with limited access to arts programming.",
     "Expanding arts access across America"),
    (1, "Performing Arts Program", "general_operating", 100000, 500000, 90,
     "Mellon's Performing Arts program supports performing arts organizations and artists in ways that sustain the conditions for artistic creation and engagement.",
     "Strengthening performing arts institutions"),
    (1, "Orchestra Capacity Building", "technical_assistance", 50000, 200000, 60,
     "Investments in the organizational infrastructure and leadership capacity of orchestras.",
     "Building organizational resilience"),
    (2, "Sphinx Venture Fund", "project", 5000, 50000, 150,
     "The Sphinx Venture Fund supports organizations engaged in diversity and inclusion work in classical music.",
     "Diversity and inclusion in classical music"),
    (3, "Orchestra Leadership Academy", "education", 15000, 75000, 100,
     "Supports professional development and leadership training for orchestra administrators and musicians.",
     "Developing the next generation of orchestra leaders"),
    (3, "Innovation and Entrepreneurship", "project", 25000, 150000, 200,
     "Grants for orchestras pursuing innovative programming, business models, and community engagement strategies.",
     "Innovation in orchestral programming"),
    (4, "Creativity and Free Expression", "general_operating", 250000, 1000000, 240,
     "Ford Foundation's arts grants center on ensuring that those who have been historically excluded can tell their own stories and have them heard.",
     "Arts as a catalyst for social change"),
    (5, "Performing Arts Program", "general_operating", 75000, 300000, 75,
     "DDCF's performing arts program supports the growth of artists and arts organizations, particularly those working in theater, contemporary dance, and jazz.",
     "Investing in artistic excellence"),
    (5, "Arts Education", "education", 50000, 150000, 135,
     "Grants to support arts education programs for young people, particularly in underserved communities.",
     "Arts education for all"),
    (6, "Organization Capacity Building", "technical_assistance", 5000, 50000, 45,
     "NYSCA capacity building grants help arts organizations strengthen their operations and sustainability.",
     "Building sustainable arts organizations in New York"),
    (6, "Arts in Education", "education", 10000, 100000, 55,
     "Supports New York arts organizations providing arts education to students across the state.",
     "Arts education across New York"),
    (6, "Special Arts Services", "general_operating", 25000, 150000, 70,
     "Supports arts service organizations that provide programs and services of statewide significance.",
     "Statewide arts services"),
    (7, "Philadelphia Cultural Fund", "general_operating", 25000, 250000, 160,
     "Pew supports established Philadelphia arts and cultural organizations with multi-year operating support.",
     "Sustaining Philadelphia's cultural sector"),
    (7, "Artistic Excellence", "project", 50000, 200000, 190,
     "Pew's Artistic Excellence grants support the creation and presentation of ambitious new work by Philadelphia artists and arts organizations.",
     "Ambitious new work in Philadelphia"),
    (0, "Research: Art Works", "project", 25000, 80000, 210,
     "NEA Research grants support applied research into the value and impact of the arts in communities.",
     "Evidence-based arts research"),
    (1, "Higher Education and Scholarship", "education", 100000, 400000, 300,
     "Mellon's Higher Education and Scholarship in the Humanities program supports foundational programs that advance humanistic inquiry.",
     "Humanities education and scholarship"),
    (3, "Futures Fund", "endowment", 50000, 250000, 365,
     "Supports orchestras in building endowment funds to ensure long-term financial sustainability.",
     "Long-term financial sustainability for orchestras"),
]


async def main():
    async with SessionLocal() as session:
        # Check if grants already exist
        from sqlalchemy import select, func
        result = await session.execute(select(func.count()).select_from(Grant))
        count = result.scalar()
        if count > 0:
            print(f"Database already has {count} grants. Skipping seed.")
            return

        # Create funders
        funder_objects = []
        for f in FUNDERS:
            funder = Funder(
                id=uuid.uuid4(),
                name=f["name"],
                type=f["type"],
                website=f.get("website"),
                description=f.get("description"),
                geographic_focus=f.get("geographic_focus"),
                arts_specific=f.get("arts_specific", True),
                giving_range_min=f.get("giving_range_min"),
                giving_range_max=f.get("giving_range_max"),
            )
            session.add(funder)
            funder_objects.append(funder)

        await session.flush()
        print(f"Created {len(funder_objects)} funders")

        # Create grants
        today = date.today()
        grant_count = 0
        for (fi, title, gtype, min_amt, max_amt, days, desc, tagline) in GRANTS:
            funder = funder_objects[fi]
            grant = Grant(
                id=uuid.uuid4(),
                funder_id=funder.id,
                title=title,
                description=desc,
                tagline=tagline,
                type=gtype,
                eligible_org_types=["symphony", "chamber_orchestra", "opera", "chorus", "performing_arts"],
                min_amount=min_amt,
                max_amount=max_amt,
                typical_amount=(min_amt + max_amt) / 2,
                deadline=today + timedelta(days=days),
                cycle_frequency="annual",
                loi_required=False,
                reporting_required=True,
                match_required=False,
                is_active=True,
                is_verified=True,
                source="manual",
            )
            session.add(grant)
            grant_count += 1

        await session.commit()
        print(f"Created {grant_count} grants")
        print("Grant database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(main())
