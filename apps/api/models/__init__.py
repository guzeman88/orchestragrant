from __future__ import annotations

import uuid
from datetime import datetime, date

import sqlalchemy as sa
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Enum, Float,
    ForeignKey, Integer, String, Text, JSON, UniqueConstraint, Index,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_AVAILABLE = True
except Exception:
    Vector = None  # type: ignore
    _VECTOR_AVAILABLE = False

from database import Base


def uuid_pk():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


def now_utc():
    return Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


def updated_at():
    return Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ─── Enums ─────────────────────────────────────────────────────────────────────

user_role_enum = Enum(
    "owner", "director", "grant_writer", "staff", "read_only",
    name="user_role", schema="auth"
)

org_type_enum = Enum(
    "symphony", "chamber_orchestra", "opera", "chorus", "performing_arts", "other",
    name="org_type"
)

subscription_tier_enum = Enum(
    "starter", "professional", "enterprise",
    name="subscription_tier"
)

subscription_status_enum = Enum(
    "active", "trialing", "past_due", "canceled",
    name="subscription_status"
)

application_stage_enum = Enum(
    "prospecting", "qualifying", "writing", "internal_review",
    "director_review", "board_approval", "ready_to_submit", "submitted",
    "under_review", "awarded", "declined", "withdrawn",
    name="application_stage", schema="applications"
)

grant_type_enum = Enum(
    "general_operating", "project", "capital", "endowment", "emergency",
    "commissioning", "education", "touring", "recording", "technical_assistance",
    name="grant_type", schema="grants"
)

funder_type_enum = Enum(
    "foundation", "government_federal", "government_state", "government_local",
    "corporation", "individual",
    name="funder_type", schema="grants"
)

doc_category_enum = Enum(
    "mission_vision", "strategic_plan", "annual_report", "audit", "form_990",
    "irs_determination", "board_list", "budget", "program_descriptions",
    "evaluation_reports", "press_kit", "policies", "other",
    name="document_category"
)

doc_processing_enum = Enum(
    "pending", "processing", "complete", "failed",
    name="document_processing_status"
)


# ─── Organizations ─────────────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = uuid_pk()
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=False)
    ein = Column(String(20), nullable=False, unique=True)
    org_type = Column(org_type_enum, nullable=False, default="symphony")
    subscription_tier = Column(subscription_tier_enum, nullable=False, default="starter")
    subscription_status = Column(subscription_status_enum, nullable=False, default="trialing")
    stripe_customer_id = Column(String(255))
    logo_url = Column(Text)
    website = Column(Text)
    primary_email = Column(String(255), nullable=False)
    phone = Column(String(50))
    address_street = Column(String(500))
    address_city = Column(String(255))
    address_state = Column(String(2))
    address_zip = Column(String(20))
    founded_year = Column(Integer)
    budget_size = Column(Float)
    staff_count = Column(Integer)
    is_onboarded = Column(Boolean, nullable=False, default=False)
    profile_completeness_score = Column(Integer, nullable=False, default=0)
    created_at = now_utc()
    updated_at = updated_at()

    # Relationships
    users = relationship("User", back_populates="org", lazy="noload")
    profile = relationship("OrgProfile", back_populates="org", uselist=False, lazy="noload")
    grants_watchlist = relationship("GrantWatchlistItem", back_populates="org", lazy="noload")
    applications = relationship("Application", back_populates="org", lazy="noload")
    documents = relationship("OrgDocument", back_populates="org", lazy="noload")


class OrgProfile(Base):
    __tablename__ = "org_profiles"

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, unique=True)
    mission = Column(Text)
    vision = Column(Text)
    programs_description = Column(Text)
    geographic_scope = Column(String(500))
    primary_artistic_focus = Column(String(500))
    performances_per_year = Column(Integer)
    audience_size = Column(Integer)
    member_musicians = Column(Integer)
    community_impact_statement = Column(Text)
    diversity_statement = Column(Text)
    updated_at = updated_at()

    org = relationship("Organization", back_populates="profile")


class BoardMember(Base):
    __tablename__ = "board_members"

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    title = Column(String(255))
    email = Column(String(255))
    is_officer = Column(Boolean, nullable=False, default=False)
    join_date = Column(Date)
    term_end_date = Column(Date)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = now_utc()


# ─── Auth ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email"),
        {"schema": "auth"},
    )

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(user_role_enum, nullable=False, default="staff")
    is_active = Column(Boolean, nullable=False, default=True)
    is_mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret = Column(String(255))  # Encrypted TOTP secret
    avatar_url = Column(Text)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    invited_at = Column(DateTime(timezone=True))
    last_login_at = Column(DateTime(timezone=True))
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True))
    created_at = now_utc()
    updated_at = updated_at()

    org = relationship("Organization", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user", lazy="noload")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "auth"}

    id = uuid_pk()
    user_id = Column(UUID(as_uuid=True), ForeignKey("auth.users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    issued_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    user = relationship("User", back_populates="refresh_tokens")


# ─── Grants ────────────────────────────────────────────────────────────────────

class Funder(Base):
    __tablename__ = "funders"
    __table_args__ = {"schema": "grants"}

    id = uuid_pk()
    name = Column(String(500), nullable=False)
    type = Column(funder_type_enum, nullable=False)
    ein = Column(String(20))
    website = Column(Text)
    primary_contact = Column(String(255))
    primary_contact_email = Column(String(255))
    primary_contact_phone = Column(String(50))
    description = Column(Text)
    geographic_focus = Column(ARRAY(String))
    arts_specific = Column(Boolean, nullable=False, default=False)
    giving_range_min = Column(Float)
    giving_range_max = Column(Float)
    total_grants_per_year = Column(Integer)
    annual_giving_total = Column(Float)
    deadline_notes = Column(Text)
    preference_notes = Column(Text)
    relationship_strength = Column(
        Enum("none", "cold", "warm", "strong", name="relationship_strength", schema="grants"),
        default="none"
    )
    last_contact_date = Column(Date)
    candid_org_id = Column(String(100))
    created_at = now_utc()
    updated_at = updated_at()

    grants = relationship("Grant", back_populates="funder", lazy="noload")


class Grant(Base):
    __tablename__ = "grants"
    __table_args__ = (
        Index("ix_grants_fts", sa.text("to_tsvector('english', coalesce(title,'') || ' ' || coalesce(description,''))"), postgresql_using="gin"),
        {"schema": "grants"},
    )

    id = uuid_pk()
    funder_id = Column(UUID(as_uuid=True), ForeignKey("grants.funders.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    type = Column(grant_type_enum, nullable=False)
    eligible_org_types = Column(ARRAY(String))
    min_amount = Column(Float)
    max_amount = Column(Float)
    typical_amount = Column(Float)
    deadline = Column(Date)
    cycle_frequency = Column(
        Enum("annual", "biannual", "rolling", "one_time", name="cycle_frequency", schema="grants")
    )
    application_url = Column(Text)
    loi_required = Column(Boolean, nullable=False, default=False)
    reporting_required = Column(Boolean, nullable=False, default=True)
    match_required = Column(Boolean, nullable=False, default=False)
    match_percentage = Column(Float)
    geographic_restrictions = Column(ARRAY(String))
    budget_size_min = Column(Float)
    budget_size_max = Column(Float)
    is_active = Column(Boolean, nullable=False, default=True)
    is_verified = Column(Boolean, nullable=False, default=False)
    last_verified_at = Column(DateTime(timezone=True))
    notes = Column(Text)
    tagline = Column(String(500))
    source = Column(Enum("candid", "grants_gov", "scraped", "manual", name="grant_source", schema="grants"))
    embedding = Column(Vector(3072)) if _VECTOR_AVAILABLE else None  # text-embedding-3-large
    created_at = now_utc()
    updated_at = updated_at()

    funder = relationship("Funder", back_populates="grants")
    watchlist_items = relationship("GrantWatchlistItem", back_populates="grant", lazy="noload")


class GrantWatchlistItem(Base):
    __tablename__ = "grant_watchlist"
    __table_args__ = (
        UniqueConstraint("org_id", "grant_id"),
        {"schema": "grants"},
    )

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    grant_id = Column(UUID(as_uuid=True), ForeignKey("grants.grants.id", ondelete="CASCADE"), nullable=False)
    added_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    notes = Column(Text)
    created_at = now_utc()

    org = relationship("Organization", back_populates="grants_watchlist")
    grant = relationship("Grant", back_populates="watchlist_items")


# ─── Applications ──────────────────────────────────────────────────────────────

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = {"schema": "applications"}

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    grant_id = Column(UUID(as_uuid=True), ForeignKey("grants.grants.id"), nullable=False)
    title = Column(String(500), nullable=False)
    stage = Column(application_stage_enum, nullable=False, default="prospecting")
    requested_amount = Column(Float)
    awarded_amount = Column(Float)
    submission_deadline = Column(DateTime(timezone=True))
    submitted_at = Column(DateTime(timezone=True))
    outcome_at = Column(DateTime(timezone=True))
    reporting_deadline = Column(DateTime(timezone=True))
    project_title = Column(String(500))
    project_description = Column(Text)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    priority = Column(
        Enum("low", "medium", "high", "critical", name="priority", schema="applications"),
        default="medium"
    )
    internal_notes = Column(Text)
    tags = Column(ARRAY(String))
    stage_history = Column(JSON, nullable=False, default=list)
    created_at = now_utc()
    updated_at = updated_at()

    org = relationship("Organization", back_populates="applications")
    grant = relationship("Grant")
    assigned_user = relationship("User", foreign_keys=[assigned_to])
    sections = relationship("ApplicationSection", back_populates="application", order_by="ApplicationSection.sort_order", lazy="noload")


class ApplicationSection(Base):
    __tablename__ = "application_sections"
    __table_args__ = {"schema": "applications"}

    id = uuid_pk()
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.applications.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    prompt = Column(Text)
    content = Column(Text)  # ProseMirror JSON string
    word_limit = Column(Integer)
    char_limit = Column(Integer)
    is_required = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    status = Column(
        Enum("not_started", "in_progress", "complete", "approved", name="section_status", schema="applications"),
        nullable=False, default="not_started"
    )
    last_edited_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    locked_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"))
    locked_at = Column(DateTime(timezone=True))
    updated_at = updated_at()

    application = relationship("Application", back_populates="sections")


# ─── Documents ─────────────────────────────────────────────────────────────────

class OrgDocument(Base):
    __tablename__ = "org_documents"

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    category = Column(doc_category_enum, nullable=False)
    file_name = Column(String(500), nullable=False)
    file_key = Column(Text, nullable=False)  # S3 key
    file_size_bytes = Column(Integer)
    mime_type = Column(String(255))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("auth.users.id"), nullable=False)
    uploaded_at = now_utc()
    processed_at = Column(DateTime(timezone=True))
    processing_status = Column(doc_processing_enum, nullable=False, default="pending")
    extracted_text_length = Column(Integer)
    year = Column(Integer)
    description = Column(Text)
    tags = Column(ARRAY(String))

    org = relationship("Organization", back_populates="documents")


# ─── Deadlines ─────────────────────────────────────────────────────────────────

class Deadline(Base):
    __tablename__ = "deadlines"

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.applications.id", ondelete="SET NULL"))
    grant_id = Column(UUID(as_uuid=True), ForeignKey("grants.grants.id", ondelete="SET NULL"))
    title = Column(String(500), nullable=False)
    deadline_at = Column(DateTime(timezone=True), nullable=False)
    type = Column(
        Enum("application", "loi", "report", "award_decision", "meeting", "other",
             name="deadline_type"),
        nullable=False, default="application"
    )
    reminder_days = Column(ARRAY(Integer), nullable=False, default=[7, 3, 1])
    notes = Column(Text)
    is_completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime(timezone=True))
    created_at = now_utc()


# ─── Awards ────────────────────────────────────────────────────────────────────

class Award(Base):
    __tablename__ = "awards"
    __table_args__ = {"schema": "awards"}

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.applications.id"), nullable=False)
    funder_id = Column(UUID(as_uuid=True), ForeignKey("grants.funders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    awarded_at = Column(Date, nullable=False)
    period_start = Column(Date)
    period_end = Column(Date)
    agreement_url = Column(Text)
    restriction_type = Column(
        Enum("unrestricted", "restricted", "project", name="restriction_type", schema="awards"),
        nullable=False, default="unrestricted"
    )
    reporting_schedule = Column(JSON, nullable=False, default=list)
    total_spent = Column(Float, nullable=False, default=0.0)
    notes = Column(Text)
    created_at = now_utc()
    updated_at = updated_at()

    application = relationship("Application")
    funder = relationship("Funder")


# ─── AI / Narrative Atoms ──────────────────────────────────────────────────────

class NarrativeAtom(Base):
    """Chunked text from org documents, used for RAG retrieval."""
    __tablename__ = "narrative_atoms"
    __table_args__ = (
        *((Index("ix_narrative_atoms_embedding", "embedding", postgresql_using="hnsw",
              postgresql_with={"m": 16, "ef_construction": 64},
              postgresql_ops={"embedding": "vector_cosine_ops"}),) if _VECTOR_AVAILABLE else ()),
        {"schema": "ai"},
    )

    id = uuid_pk()
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("org_documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(3072)) if _VECTOR_AVAILABLE else None
    token_count = Column(Integer)
    category = Column(doc_category_enum)
    created_at = now_utc()
