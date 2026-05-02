from __future__ import annotations

from datetime import datetime, date
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator


class BaseSchema(BaseModel):
    model_config = {"from_attributes": True, "populate_by_name": True}


# ─── Auth ──────────────────────────────────────────────────────────────────────

class LoginRequest(BaseSchema):
    email: str  # str not EmailStr so any input returns 401 not 422
    password: str = Field(min_length=1)
    totp_code: Optional[str] = None


class LoginResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserRead"
    org: "OrgRead"


class RefreshRequest(BaseSchema):
    refresh_token: str


class RefreshResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int


class LogoutRequest(BaseSchema):
    refresh_token: Optional[str] = None


class MfaSetupResponse(BaseSchema):
    secret: str
    qr_data_uri: str


class MfaVerifyRequest(BaseSchema):
    totp_code: str = Field(min_length=6, max_length=6)


# ─── Users ─────────────────────────────────────────────────────────────────────

class UserRead(BaseSchema):
    id: UUID
    email: str
    first_name: str
    last_name: str
    role: str
    org_id: UUID
    is_active: bool
    is_mfa_enabled: bool
    avatar_url: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseSchema):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar_url: Optional[str] = None


class InviteUserRequest(BaseSchema):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: str = "staff"

    @model_validator(mode="after")
    def validate_role(self):
        valid = {"director", "grant_writer", "staff", "read_only"}
        if self.role not in valid:
            raise ValueError(f"role must be one of: {valid}")
        return self


# ─── Organizations ─────────────────────────────────────────────────────────────

class OrgRead(BaseSchema):
    id: UUID
    name: str
    legal_name: str
    ein: str
    org_type: str
    subscription_tier: str
    subscription_status: str
    logo_url: Optional[str] = None
    website: Optional[str] = None
    primary_email: str
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = None
    address_zip: Optional[str] = None
    founded_year: Optional[int] = None
    budget_size: Optional[float] = None
    staff_count: Optional[int] = None
    is_onboarded: bool
    profile_completeness_score: int
    created_at: datetime
    updated_at: datetime


class OrgUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(None, min_length=1, max_length=255)
    website: Optional[str] = None
    primary_email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address_street: Optional[str] = None
    address_city: Optional[str] = None
    address_state: Optional[str] = Field(None, min_length=2, max_length=2)
    address_zip: Optional[str] = None
    founded_year: Optional[int] = Field(None, ge=1600, le=2100)
    budget_size: Optional[float] = Field(None, ge=0)
    staff_count: Optional[int] = Field(None, ge=0)


class OrgProfileRead(BaseSchema):
    id: UUID
    org_id: UUID
    mission: Optional[str] = None
    vision: Optional[str] = None
    programs_description: Optional[str] = None
    geographic_scope: Optional[str] = None
    primary_artistic_focus: Optional[str] = None
    performances_per_year: Optional[int] = None
    audience_size: Optional[int] = None
    member_musicians: Optional[int] = None
    community_impact_statement: Optional[str] = None
    diversity_statement: Optional[str] = None
    updated_at: datetime


class OrgProfileUpdate(BaseSchema):
    mission: Optional[str] = Field(None, max_length=2000)
    vision: Optional[str] = Field(None, max_length=2000)
    programs_description: Optional[str] = Field(None, max_length=5000)
    geographic_scope: Optional[str] = Field(None, max_length=500)
    primary_artistic_focus: Optional[str] = Field(None, max_length=500)
    performances_per_year: Optional[int] = Field(None, ge=0, le=1000)
    audience_size: Optional[int] = Field(None, ge=0)
    member_musicians: Optional[int] = Field(None, ge=0)
    community_impact_statement: Optional[str] = Field(None, max_length=2000)
    diversity_statement: Optional[str] = Field(None, max_length=2000)


# ─── Grants ────────────────────────────────────────────────────────────────────

class FunderRead(BaseSchema):
    id: UUID
    name: str
    type: str
    ein: Optional[str] = None
    website: Optional[str] = None
    primary_contact: Optional[str] = None
    primary_contact_email: Optional[str] = None
    arts_specific: bool
    giving_range_min: Optional[float] = None
    giving_range_max: Optional[float] = None
    relationship_strength: Optional[str] = None
    created_at: datetime


class GrantRead(BaseSchema):
    id: UUID
    funder_id: UUID
    funder: Optional[FunderRead] = None
    title: str
    description: Optional[str] = None
    tagline: Optional[str] = None
    type: str
    eligible_org_types: Optional[list[str]] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    typical_amount: Optional[float] = None
    deadline: Optional[date] = None
    cycle_frequency: Optional[str] = None
    application_url: Optional[str] = None
    loi_required: bool
    reporting_required: bool
    match_required: bool
    match_percentage: Optional[float] = None
    geographic_restrictions: Optional[list[str]] = None
    budget_size_min: Optional[float] = None
    budget_size_max: Optional[float] = None
    notes: Optional[str] = None
    is_active: bool
    is_verified: bool
    last_verified_at: Optional[datetime] = None
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class GrantSearch(BaseSchema):
    query: Optional[str] = None
    type: Optional[str] = None
    funder_type: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    deadline_before: Optional[str] = None
    deadline_after: Optional[str] = None
    arts_specific: Optional[bool] = None
    is_active: bool = True
    page: int = Field(1, ge=1)
    page_size: int = Field(25, ge=1, le=100)
    sort_by: str = "relevance"
    sort_order: str = "desc"


class PaginatedGrants(BaseSchema):
    items: list[GrantRead]
    total: int
    page: int
    page_size: int
    has_more: bool


# ─── Applications ──────────────────────────────────────────────────────────────

class ApplicationSectionRead(BaseSchema):
    id: UUID
    application_id: UUID
    title: str
    prompt: Optional[str] = None
    content: Optional[str] = None
    word_limit: Optional[int] = None
    char_limit: Optional[int] = None
    is_required: bool
    sort_order: int
    status: str
    last_edited_by: Optional[UUID] = None
    locked_by: Optional[UUID] = None
    locked_at: Optional[datetime] = None
    updated_at: datetime


class ApplicationRead(BaseSchema):
    id: UUID
    org_id: UUID
    grant_id: UUID
    grant: Optional[GrantRead] = None
    title: str
    stage: str
    requested_amount: Optional[float] = None
    awarded_amount: Optional[float] = None
    submission_deadline: Optional[datetime] = None
    submitted_at: Optional[datetime] = None
    outcome_at: Optional[datetime] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    assigned_user: Optional[UserRead] = None
    priority: Optional[str] = None
    tags: Optional[list[str]] = None
    stage_history: list = []
    created_at: datetime
    updated_at: datetime


class ApplicationCreate(BaseSchema):
    grant_id: UUID
    title: str = Field(min_length=1, max_length=500)
    requested_amount: Optional[float] = Field(None, ge=0)
    submission_deadline: Optional[datetime] = None
    project_title: Optional[str] = Field(None, max_length=500)
    project_description: Optional[str] = Field(None, max_length=5000)
    assigned_to: Optional[UUID] = None
    priority: Optional[str] = "medium"


class ApplicationUpdate(BaseSchema):
    stage: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    requested_amount: Optional[float] = Field(None, ge=0)
    submission_deadline: Optional[datetime] = None
    project_title: Optional[str] = None
    project_description: Optional[str] = None
    assigned_to: Optional[UUID] = None
    priority: Optional[str] = None
    internal_notes: Optional[str] = None
    tags: Optional[list[str]] = None


class StageTransitionRequest(BaseSchema):
    new_stage: str
    note: Optional[str] = None


class SectionUpdate(BaseSchema):
    content: Optional[str] = None
    status: Optional[str] = None


class PaginatedApplications(BaseSchema):
    items: list[ApplicationRead]
    total: int
    page: int
    page_size: int
    has_more: bool


# ─── Documents ─────────────────────────────────────────────────────────────────

class PresignedUploadRequest(BaseSchema):
    file_name: str = Field(min_length=1, max_length=500)
    mime_type: str = Field(min_length=1, max_length=255)
    file_size_bytes: int = Field(ge=1, le=52_428_800)  # 50 MB max
    category: str
    year: Optional[int] = Field(None, ge=1900, le=2100)
    description: Optional[str] = None


class PresignedUploadResponse(BaseSchema):
    upload_url: str
    document_id: UUID
    expires_in: int


class DocumentRead(BaseSchema):
    id: UUID
    org_id: UUID
    category: str
    file_name: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime
    processing_status: str
    year: Optional[int] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None


# ─── Deadlines ─────────────────────────────────────────────────────────────────

class DeadlineRead(BaseSchema):
    id: UUID
    org_id: UUID
    application_id: Optional[UUID] = None
    grant_id: Optional[UUID] = None
    title: str
    deadline_at: datetime
    type: str
    reminder_days: list[int]
    notes: Optional[str] = None
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime


class DeadlineCreate(BaseSchema):
    title: str = Field(min_length=1, max_length=500)
    deadline_at: datetime
    type: str = "application"
    application_id: Optional[UUID] = None
    grant_id: Optional[UUID] = None
    reminder_days: list[int] = [7, 3, 1]
    notes: Optional[str] = None
