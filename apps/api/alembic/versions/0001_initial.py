"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-01
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, ARRAY
try:
    import pgvector.sqlalchemy
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions (already created by postgres-init.sql, but idempotent) ──
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute("""
        DO $$ BEGIN
            CREATE EXTENSION IF NOT EXISTS vector;
        EXCEPTION WHEN OTHERS THEN
            RAISE NOTICE 'pgvector not available, AI embedding features disabled';
        END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE EXTENSION IF NOT EXISTS pg_trgm;
        EXCEPTION WHEN OTHERS THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE EXTENSION IF NOT EXISTS btree_gin;
        EXCEPTION WHEN OTHERS THEN NULL; END $$
    """)

    # ── Schemas ─────────────────────────────────────────────────────────────
    for schema in ("auth", "grants", "applications", "awards", "ai", "discovery"):
        op.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    # ── Enums ───────────────────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE auth.user_role AS ENUM (
                'owner','director','grant_writer','staff','read_only'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE org_type AS ENUM (
                'symphony','chamber_orchestra','opera','chorus','performing_arts','other'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE subscription_tier AS ENUM ('starter','professional','enterprise');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE subscription_status AS ENUM ('active','trialing','past_due','canceled');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE applications.application_stage AS ENUM (
                'prospecting','qualifying','writing','internal_review',
                'director_review','board_approval','ready_to_submit','submitted',
                'under_review','awarded','declined','withdrawn'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE grants.grant_type AS ENUM (
                'general_operating','project','capital','endowment','emergency',
                'commissioning','education','touring','recording','technical_assistance'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE grants.funder_type AS ENUM (
                'foundation','government_federal','government_state','government_local',
                'corporation','individual'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_category AS ENUM (
                'mission_vision','strategic_plan','annual_report','audit','form_990',
                'irs_determination','board_list','budget','program_descriptions',
                'evaluation_reports','press_kit','policies','other'
            );
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE document_processing_status AS ENUM ('pending','processing','complete','failed');
        EXCEPTION WHEN duplicate_object THEN NULL; END $$
    """)

    # ── Organizations ────────────────────────────────────────────────────────
    op.create_table(
        "organizations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("ein", sa.String(20), nullable=False, unique=True),
        sa.Column("org_type", sa.Text, nullable=False, server_default="symphony"),
        sa.Column("subscription_tier", sa.Text, nullable=False, server_default="starter"),
        sa.Column("subscription_status", sa.Text, nullable=False, server_default="trialing"),
        sa.Column("stripe_customer_id", sa.String(255)),
        sa.Column("stripe_subscription_id", sa.String(255)),
        sa.Column("logo_url", sa.Text),
        sa.Column("website", sa.Text),
        sa.Column("primary_email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50)),
        sa.Column("address_street", sa.String(500)),
        sa.Column("address_city", sa.String(255)),
        sa.Column("address_state", sa.String(2)),
        sa.Column("address_zip", sa.String(20)),
        sa.Column("founded_year", sa.Integer),
        sa.Column("budget_size", sa.Float),
        sa.Column("staff_count", sa.Integer),
        sa.Column("is_onboarded", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("profile_completeness_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "org_profiles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("mission", sa.Text),
        sa.Column("vision", sa.Text),
        sa.Column("programs_description", sa.Text),
        sa.Column("geographic_scope", sa.String(500)),
        sa.Column("primary_artistic_focus", sa.String(500)),
        sa.Column("performances_per_year", sa.Integer),
        sa.Column("audience_size", sa.Integer),
        sa.Column("member_musicians", sa.Integer),
        sa.Column("community_impact_statement", sa.Text),
        sa.Column("diversity_statement", sa.Text),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_table(
        "board_members",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("email", sa.String(255)),
        sa.Column("is_officer", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("join_date", sa.Date),
        sa.Column("term_end_date", sa.Date),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Auth ────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("role", sa.Text, nullable=False, server_default="staff"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_mfa_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("mfa_secret", sa.String(255)),
        sa.Column("avatar_url", sa.Text),
        sa.Column("invited_by", UUID(as_uuid=True)),
        sa.Column("invited_at", sa.DateTime(timezone=True)),
        sa.Column("last_login_at", sa.DateTime(timezone=True)),
        sa.Column("failed_login_attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="auth",
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True)),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="auth",
    )

    op.create_index("ix_auth_refresh_tokens_user_id", "refresh_tokens", ["user_id"], schema="auth")

    # ── Grants ──────────────────────────────────────────────────────────────
    op.create_table(
        "funders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("type", sa.Text),
        sa.Column("website", sa.Text),
        sa.Column("description", sa.Text),
        sa.Column("ein", sa.String(20)),
        sa.Column("address_city", sa.String(255)),
        sa.Column("address_state", sa.String(2)),
        sa.Column("phone", sa.String(50)),
        sa.Column("contact_email", sa.String(255)),
        sa.Column("total_giving", sa.Float),
        sa.Column("candid_id", sa.String(100), unique=True),
        sa.Column("grants_gov_agency_code", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="grants",
    )

    op.create_table(
        "grants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("funder_id", UUID(as_uuid=True), sa.ForeignKey("grants.funders.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("eligibility_requirements", sa.Text),
        sa.Column("type", sa.Text),
        sa.Column("min_amount", sa.Float),
        sa.Column("max_amount", sa.Float),
        sa.Column("deadline", sa.Date),
        sa.Column("open_date", sa.Date),
        sa.Column("url", sa.Text),
        sa.Column("arts_specific", sa.Boolean, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("source", sa.String(100)),
        sa.Column("external_id", sa.String(255)),
        sa.Column("fts", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="grants",
    )
    # Add embedding column only if pgvector is available
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
                ALTER TABLE grants.grants ADD COLUMN IF NOT EXISTS embedding vector(3072);
            END IF;
        END $$
    """)

    op.execute("""
        ALTER TABLE grants.grants
        ADD COLUMN IF NOT EXISTS search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('english', coalesce(title, '') || ' ' || coalesce(description, '') || ' ' || coalesce(eligibility_requirements, ''))
        ) STORED
    """)
    op.create_index("ix_grants_grants_search_vector", "grants", [sa.text("search_vector")], postgresql_using="gin", schema="grants")
    op.create_index("ix_grants_grants_deadline", "grants", ["deadline"], schema="grants")
    op.create_index("ix_grants_grants_is_active", "grants", ["is_active"], schema="grants")
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
                EXECUTE 'CREATE INDEX IF NOT EXISTS ix_grants_grants_embedding ON grants.grants USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)';
            END IF;
        END $$
    """)

    op.create_table(
        "grant_watchlist",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("grant_id", UUID(as_uuid=True), sa.ForeignKey("grants.grants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("org_id", "grant_id", name="uq_watchlist_org_grant"),
        schema="grants",
    )

    # ── Applications ─────────────────────────────────────────────────────────
    op.create_table(
        "applications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("grant_id", UUID(as_uuid=True), sa.ForeignKey("grants.grants.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("stage", sa.Text, nullable=False, server_default="prospecting"),
        sa.Column("stage_history", sa.JSON, server_default="[]"),
        sa.Column("deadline", sa.Date),
        sa.Column("request_amount", sa.Float),
        sa.Column("award_amount", sa.Float),
        sa.Column("lead_writer", sa.String(255)),
        sa.Column("internal_notes", sa.Text),
        sa.Column("submission_url", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="applications",
    )

    op.create_index("ix_applications_applications_org_id", "applications", ["org_id"], schema="applications")
    op.create_index("ix_applications_applications_stage", "applications", ["stage"], schema="applications")

    op.create_table(
        "application_sections",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("application_id", UUID(as_uuid=True), sa.ForeignKey("applications.applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("prompt", sa.Text),
        sa.Column("content", sa.Text),
        sa.Column("word_limit", sa.Integer),
        sa.Column("char_limit", sa.Integer),
        sa.Column("status", sa.Text, server_default="empty"),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_by", UUID(as_uuid=True)),
        sa.Column("locked_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="applications",
    )

    # ── Documents ────────────────────────────────────────────────────────────
    op.create_table(
        "org_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("file_key", sa.String(1000), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size_bytes", sa.Integer),
        sa.Column("category", sa.Text, nullable=False, server_default="other"),
        sa.Column("year", sa.Integer),
        sa.Column("description", sa.Text),
        sa.Column("processing_status", sa.Text, nullable=False, server_default="pending"),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # ── Deadlines ────────────────────────────────────────────────────────────
    op.create_table(
        "deadlines",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", UUID(as_uuid=True), sa.ForeignKey("applications.applications.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("type", sa.String(100), nullable=False, server_default="submission"),
        sa.Column("reminder_days", ARRAY(sa.Integer), server_default="{}"),
        sa.Column("is_completed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    op.create_index("ix_deadlines_org_id", "deadlines", ["org_id"])
    op.create_index("ix_deadlines_deadline_at", "deadlines", ["deadline_at"])

    # ── Awards ───────────────────────────────────────────────────────────────
    op.create_table(
        "awards",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("application_id", UUID(as_uuid=True), sa.ForeignKey("applications.applications.id", ondelete="SET NULL")),
        sa.Column("grant_id", UUID(as_uuid=True), sa.ForeignKey("grants.grants.id", ondelete="SET NULL")),
        sa.Column("amount", sa.Float, nullable=False),
        sa.Column("received_date", sa.Date),
        sa.Column("project_period_start", sa.Date),
        sa.Column("project_period_end", sa.Date),
        sa.Column("grant_agreement_url", sa.Text),
        sa.Column("reporting_schedule", sa.JSON, server_default="[]"),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="awards",
    )

    # ── AI ───────────────────────────────────────────────────────────────────
    op.create_table(
        "narrative_atoms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("org_documents.id", ondelete="SET NULL")),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        schema="ai",
    )
    # Add embedding column only if pgvector is available
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
                ALTER TABLE ai.narrative_atoms ADD COLUMN IF NOT EXISTS embedding vector(3072);
                EXECUTE 'CREATE INDEX IF NOT EXISTS ix_ai_narrative_atoms_embedding ON ai.narrative_atoms USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)';
            END IF;
        END $$
    """)
    op.create_index("ix_ai_narrative_atoms_org_id", "narrative_atoms", ["org_id"], schema="ai")

    # ── Discovery ────────────────────────────────────────────────────────────
    op.create_table(
        "scrape_runs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("grants_found", sa.Integer, server_default="0"),
        sa.Column("grants_new", sa.Integer, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="running"),
        sa.Column("error", sa.Text),
        schema="discovery",
    )

    # ── update_at triggers ────────────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION set_updated_at()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN NEW.updated_at = now(); RETURN NEW; END;
        $$
    """)
    for tbl, schema in [
        ("organizations", "public"),
        ("grants", "grants"),
        ("applications", "applications"),
        ("application_sections", "applications"),
    ]:
        op.execute(f"""
            CREATE TRIGGER trg_{tbl}_updated_at
            BEFORE UPDATE ON {schema}.{tbl}
            FOR EACH ROW EXECUTE FUNCTION set_updated_at()
        """)


def downgrade() -> None:
    for schema in ("discovery", "ai", "awards", "applications", "grants", "auth"):
        op.execute(f"DROP SCHEMA IF EXISTS {schema} CASCADE")
    for tbl in ("deadlines", "org_documents", "board_members", "org_profiles", "organizations"):
        op.execute(f"DROP TABLE IF EXISTS {tbl} CASCADE")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at CASCADE")
