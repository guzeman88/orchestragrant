"""
One-time script to seed the first organization and admin user.
Run from apps/api/ with the venv active:
  python seed_admin.py
"""
import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from config import settings
from services.auth_service import hash_password

# ── Config ────────────────────────────────────────────────────────────────────
ORG_NAME  = "Demo Arts Organization"
ORG_SLUG  = "demo-arts-org"
ADMIN_FIRST = "Admin"
ADMIN_LAST  = "User"
ADMIN_EMAIL = "admin@orchestragrant.dev"
ADMIN_PASS  = "SecureDemo123!"
# ─────────────────────────────────────────────────────────────────────────────


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    org_id  = uuid.uuid4()
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    async with async_session() as session:
        async with session.begin():
            await session.execute(
                __import__("sqlalchemy").text("""
                    INSERT INTO organizations
                        (id, name, legal_name, ein, org_type,
                         subscription_tier, subscription_status,
                         primary_email, is_onboarded, profile_completeness_score,
                         created_at, updated_at)
                    VALUES
                        (:id, :name, :legal_name, :ein, 'performing_arts',
                         'starter', 'trialing',
                         :email, false, 0,
                         :now, :now)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": org_id, "name": ORG_NAME,
                    "legal_name": ORG_NAME, "ein": "00-0000000",
                    "email": ADMIN_EMAIL, "now": now,
                },
            )
            # Fetch the org id (may already exist)
            row = (await session.execute(
                __import__("sqlalchemy").text("SELECT id FROM organizations WHERE primary_email = :email"),
                {"email": ADMIN_EMAIL},
            )).fetchone()
            org_id = row[0]

            await session.execute(
                __import__("sqlalchemy").text("""
                    INSERT INTO auth.users
                        (id, org_id, email, password_hash, first_name, last_name,
                         role, is_active, is_mfa_enabled, failed_login_attempts,
                         created_at, updated_at)
                    VALUES
                        (:id, :org_id, :email, :pw, :first, :last,
                         'owner', true, false, 0,
                         :now, :now)
                    ON CONFLICT (email) DO NOTHING
                """),
                {
                    "id": user_id,
                    "org_id": org_id,
                    "email": ADMIN_EMAIL,
                    "pw": hash_password(ADMIN_PASS),
                    "first": ADMIN_FIRST,
                    "last": ADMIN_LAST,
                    "now": now,
                },
            )

    await engine.dispose()
    print(f"✓ Organization: '{ORG_NAME}' (slug={ORG_SLUG})")
    print(f"✓ Admin user: {ADMIN_EMAIL} / {ADMIN_PASS}")
    print("  Login at: http://localhost:8001/v1/auth/login")


if __name__ == "__main__":
    asyncio.run(seed())
