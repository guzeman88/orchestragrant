# Database Schema

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Database:** PostgreSQL 16 with pgvector extension  
**Last Updated:** 2026-05-01

---

## Conventions

- All tables use `uuid` primary keys (generated via `gen_random_uuid()`)
- All tables include `created_at` and `updated_at` timestamps with timezone
- Soft deletes via `deleted_at` nullable timestamp (no hard deletes on critical records)
- All foreign keys include `ON DELETE RESTRICT` unless noted otherwise
- `JSONB` used for flexible, schema-variable fields
- Enum types defined as PostgreSQL `ENUM` for enforced constraint

---

## Extensions

```sql
CREATE EXTENSION IF NOT EXISTS "pgcrypto";   -- gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- trigram indexes for fuzzy search
CREATE EXTENSION IF NOT EXISTS "unaccent";   -- accent-insensitive search
```

---

## Schema: `public` (Core)

---

### `organizations`

The root entity. All other records belong to an organization.

```sql
CREATE TABLE organizations (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    TEXT NOT NULL,
    legal_name              TEXT NOT NULL,
    ein                     CHAR(10),                        -- format: XX-XXXXXXX
    irs_determination_date  DATE,
    ntee_code               VARCHAR(10),                     -- NTEE classification code
    fiscal_year_end_month   SMALLINT NOT NULL DEFAULT 6,     -- 1=Jan, 6=Jun, etc.
    website_url             TEXT,
    phone                   TEXT,
    email                   TEXT,
    address_line1           TEXT,
    address_line2           TEXT,
    city                    TEXT,
    state                   CHAR(2),
    zip                     VARCHAR(10),
    county                  TEXT,
    country                 CHAR(2) NOT NULL DEFAULT 'US',
    service_area            JSONB,                           -- {cities: [], counties: [], states: [], zips: []}
    founded_year            SMALLINT,
    ensemble_size_min       SMALLINT,                        -- minimum per-service musicians
    ensemble_size_max       SMALLINT,                        -- maximum per-service musicians
    instrumentation         JSONB,                           -- {strings: 24, woodwinds: 8, ...}
    per_service_model       BOOLEAN NOT NULL DEFAULT TRUE,
    stripe_customer_id      TEXT,
    subscription_tier       TEXT,                            -- 'starter' | 'professional' | 'enterprise'
    subscription_status     TEXT,
    storage_used_bytes      BIGINT NOT NULL DEFAULT 0,
    storage_quota_bytes     BIGINT NOT NULL DEFAULT 53687091200, -- 50 GB default
    profile_completed_at    TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ
);

CREATE INDEX idx_organizations_ein ON organizations (ein) WHERE ein IS NOT NULL;
CREATE INDEX idx_organizations_state ON organizations (state);
```

---

### `org_profiles`

Rich narrative and programmatic data for the organization. Separated from `organizations` to allow versioning and to keep the root table lean.

```sql
CREATE TABLE org_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID NOT NULL REFERENCES organizations(id),
    
    -- Mission & Identity
    mission_short           TEXT,    -- 30 words max
    mission_medium          TEXT,    -- 100 words max
    mission_long            TEXT,    -- 300 words max
    vision_statement        TEXT,
    values_statement        TEXT,
    organizational_history  TEXT,    -- full narrative
    history_milestones      JSONB,   -- [{year: 2005, event: "Founded"}]
    
    -- Programs
    programs                JSONB,   -- [{name, description, participants, dates, outcomes}]
    partnerships            JSONB,   -- [{org_name, description, type}]
    awards_recognition      JSONB,   -- [{name, year, grantor}]
    
    -- Diversity & Equity
    dei_statement           TEXT,
    dei_demographic_data    JSONB,   -- {board: {pct_bipoc: 30}, staff: {pct_bipoc: 25}, ...}
    accessibility_statement TEXT,
    
    -- Strategic Plan
    strategic_plan_summary  TEXT,
    strategic_priorities    JSONB,   -- [{priority, description}]
    
    -- Community
    community_need_statement TEXT,
    population_served        TEXT,
    annual_attendance        INTEGER,
    annual_participants_served INTEGER,
    
    version                 INTEGER NOT NULL DEFAULT 1,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_org_profiles_org_id ON org_profiles (org_id);
```

---

### `org_financials`

One row per fiscal year per organization.

```sql
CREATE TABLE org_financials (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                      UUID NOT NULL REFERENCES organizations(id),
    fiscal_year                 SMALLINT NOT NULL,
    total_revenue               NUMERIC(12,2),
    total_expenses              NUMERIC(12,2),
    net_assets_end              NUMERIC(12,2),
    operating_budget            NUMERIC(12,2),
    revenue_breakdown           JSONB,   -- {earned: 45000, grants: 120000, individual: 30000, ...}
    expense_breakdown           JSONB,   -- {artistic: 80000, admin: 40000, marketing: 20000, ...}
    has_audit                   BOOLEAN NOT NULL DEFAULT FALSE,
    audit_firm                  TEXT,
    irs_990_filed               BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (org_id, fiscal_year)
);

CREATE INDEX idx_org_financials_org_id ON org_financials (org_id);
```

---

### `board_members`

```sql
CREATE TABLE board_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    title           TEXT,                  -- "President", "Treasurer", etc.
    employer        TEXT,
    employer_title  TEXT,
    bio             TEXT,
    email           TEXT,
    phone           TEXT,
    term_start      DATE,
    term_end        DATE,
    is_officer      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_board_members_org_id ON board_members (org_id);
```

---

### `staff_members`

```sql
CREATE TABLE staff_members (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    title           TEXT NOT NULL,
    bio             TEXT,
    email           TEXT,
    is_artistic     BOOLEAN NOT NULL DEFAULT FALSE,  -- artistic leadership flag
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_staff_members_org_id ON staff_members (org_id);
```

---

### `concert_seasons`

```sql
CREATE TABLE concert_seasons (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES organizations(id),
    season_label        TEXT NOT NULL,       -- "2025-2026 Season"
    start_date          DATE,
    end_date            DATE,
    total_concerts      SMALLINT,
    total_attendance    INTEGER,
    programs            JSONB,               -- [{title, composers, date, venue, attendance}]
    notable_works       JSONB,               -- [{composer, work, premiere_type}]
    guest_artists       JSONB,               -- [{name, instrument_or_voice, concert_title}]
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_concert_seasons_org_id ON concert_seasons (org_id);
```

---

### `documents`

Master document registry. Physical files live in S3; this table is the metadata index.

```sql
CREATE TYPE document_type AS ENUM (
    'irs_990', 'audit', 'budget', 'determination_letter',
    'prior_application', 'letter_of_support', 'board_list',
    'financial_statement', 'media_photo', 'media_video', 'media_audio',
    'grant_agreement', 'report', 'other'
);

CREATE TYPE document_status AS ENUM ('uploading', 'processing', 'indexed', 'error');

CREATE TABLE documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    name            TEXT NOT NULL,
    doc_type        document_type NOT NULL,
    status          document_status NOT NULL DEFAULT 'uploading',
    file_size_bytes BIGINT,
    mime_type       TEXT,
    s3_key          TEXT NOT NULL,
    s3_bucket       TEXT NOT NULL,
    fiscal_year     SMALLINT,              -- for 990s, audits, budgets
    description     TEXT,
    tags            TEXT[],
    parsed_text     TEXT,                  -- extracted text content
    page_count      INTEGER,
    version         INTEGER NOT NULL DEFAULT 1,
    parent_doc_id   UUID REFERENCES documents(id),  -- for versioning
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

CREATE INDEX idx_documents_org_id ON documents (org_id);
CREATE INDEX idx_documents_doc_type ON documents (org_id, doc_type);
CREATE INDEX idx_documents_tags ON documents USING GIN (tags);
CREATE INDEX idx_documents_parsed_text ON documents USING GIN (to_tsvector('english', coalesce(parsed_text, '')));
```

---

## Schema: `grants` (Grant Intelligence)

---

### `funders`

The grantmaking organization.

```sql
CREATE TYPE funder_type AS ENUM (
    'federal', 'state', 'local_municipal', 'private_foundation',
    'corporate', 'community_foundation', 'individual', 'other'
);

CREATE TABLE funders (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name                    TEXT NOT NULL,
    legal_name              TEXT,
    funder_type             funder_type NOT NULL,
    ein                     CHAR(10),
    website_url             TEXT,
    giving_portal_url       TEXT,
    logo_url                TEXT,
    description             TEXT,
    founded_year            SMALLINT,
    headquarters_city       TEXT,
    headquarters_state      CHAR(2),
    total_giving_annual     NUMERIC(14,2),     -- most recent year from 990
    priorities              JSONB,             -- [{area, description, current_focus}]
    notes                   TEXT,              -- internal intelligence notes
    candid_org_id           TEXT,              -- Candid/GuideStar identifier
    last_990_year           SMALLINT,
    last_verified_at        TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ
);

CREATE INDEX idx_funders_type ON funders (funder_type);
CREATE INDEX idx_funders_name ON funders USING GIN (to_tsvector('english', name));
CREATE INDEX idx_funders_ein ON funders (ein) WHERE ein IS NOT NULL;
```

---

### `funder_contacts`

Program officers and key contacts at each funder.

```sql
CREATE TABLE funder_contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    funder_id       UUID NOT NULL REFERENCES funders(id),
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    title           TEXT,
    email           TEXT,
    phone           TEXT,
    linkedin_url    TEXT,
    notes           TEXT,
    is_primary      BOOLEAN NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_funder_contacts_funder_id ON funder_contacts (funder_id);
```

---

### `grants`

The core grant record. Each row represents a specific grant program from a funder.

```sql
CREATE TYPE grant_type AS ENUM (
    'general_operating', 'project', 'capital', 'capacity_building',
    'commission', 'residency', 'touring', 'education', 'emergency', 'other'
);

CREATE TYPE grant_cycle_type AS ENUM (
    'annual', 'biannual', 'quarterly', 'rolling', 'irregular', 'one_time'
);

CREATE TYPE application_format AS ENUM (
    'online_portal', 'pdf_email', 'postal', 'common_grant_application', 'other'
);

CREATE TABLE grants (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    funder_id                   UUID NOT NULL REFERENCES funders(id),
    name                        TEXT NOT NULL,
    program_name                TEXT,
    grant_type                  grant_type NOT NULL,
    description                 TEXT,
    guidelines_url              TEXT,
    guidelines_s3_key           TEXT,        -- archived PDF snapshot
    application_portal_url      TEXT,
    application_format          application_format,
    
    -- Eligibility
    eligible_org_types          TEXT[],      -- ['501c3', 'fiscally_sponsored', 'government']
    geographic_restriction      TEXT,        -- 'national' | 'state:CA' | 'city:Chicago' etc.
    geographic_states           CHAR(2)[],
    geographic_cities           TEXT[],
    budget_min                  NUMERIC(12,2),
    budget_max                  NUMERIC(12,2),
    min_years_in_operation      SMALLINT,
    membership_required         TEXT,        -- e.g. 'League of American Orchestras'
    mission_focus_required      TEXT,
    prior_applicant_restriction TEXT,        -- 'first_time_only' | 'previous_grantee_required' | null
    
    -- Award
    award_min                   NUMERIC(10,2),
    award_max                   NUMERIC(10,2),
    award_typical               NUMERIC(10,2),
    match_required_pct          SMALLINT,    -- 0-100
    match_in_kind_acceptable    BOOLEAN NOT NULL DEFAULT FALSE,
    indirect_cost_allowed       BOOLEAN,
    indirect_cost_rate_cap      NUMERIC(5,2),
    multi_year_available        BOOLEAN NOT NULL DEFAULT FALSE,
    renewable                   BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Application Requirements
    loi_required                BOOLEAN NOT NULL DEFAULT FALSE,
    loi_guidelines              TEXT,
    required_sections           JSONB,       -- [{name, description, word_limit, char_limit, required: true}]
    required_attachments        JSONB,       -- [{name, description, format, required: true}]
    work_sample_required        BOOLEAN NOT NULL DEFAULT FALSE,
    work_sample_specs           JSONB,
    references_required         BOOLEAN NOT NULL DEFAULT FALSE,
    references_count            SMALLINT,
    
    -- Cycle
    cycle_type                  grant_cycle_type,
    loi_deadline_typical        TEXT,        -- e.g. "First Friday of February"
    application_deadline_typical TEXT,       -- e.g. "March 1"
    notification_period_weeks   SMALLINT,
    
    -- Intelligence
    awards_per_cycle_typical    SMALLINT,
    total_dollars_per_cycle     NUMERIC(12,2),
    competitiveness_score       SMALLINT,    -- 1-5 (1=very competitive, 5=less competitive)
    last_verified_at            TIMESTAMPTZ,
    verified_by_user_id         UUID REFERENCES users(id),
    discovery_source            TEXT,        -- 'grants_gov' | 'candid' | 'scraper' | 'manual'
    external_id                 TEXT,        -- ID from source system (e.g. Grants.gov opportunity number)
    is_active                   BOOLEAN NOT NULL DEFAULT TRUE,
    tags                        TEXT[],
    
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at                  TIMESTAMPTZ
);

CREATE INDEX idx_grants_funder_id ON grants (funder_id);
CREATE INDEX idx_grants_grant_type ON grants (grant_type);
CREATE INDEX idx_grants_geographic_states ON grants USING GIN (geographic_states);
CREATE INDEX idx_grants_tags ON grants USING GIN (tags);
CREATE INDEX idx_grants_active ON grants (is_active) WHERE is_active = TRUE;
CREATE INDEX idx_grants_name_search ON grants USING GIN (to_tsvector('english', name || ' ' || coalesce(description, '')));
```

---

### `grant_cycles`

A specific occurrence of a grant's application cycle.

```sql
CREATE TABLE grant_cycles (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grant_id            UUID NOT NULL REFERENCES grants(id),
    fiscal_year         SMALLINT NOT NULL,
    loi_deadline        DATE,
    application_deadline DATE,
    notification_date   DATE,
    grant_period_start  DATE,
    grant_period_end    DATE,
    guidelines_url      TEXT,
    guidelines_s3_key   TEXT,
    notes               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (grant_id, fiscal_year)
);

CREATE INDEX idx_grant_cycles_grant_id ON grant_cycles (grant_id);
CREATE INDEX idx_grant_cycles_deadline ON grant_cycles (application_deadline);
```

---

### `grant_watchlist`

Per-organization watchlist of grants they want to monitor.

```sql
CREATE TABLE grant_watchlist (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID NOT NULL REFERENCES organizations(id),
    grant_id    UUID NOT NULL REFERENCES grants(id),
    notes       TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (org_id, grant_id)
);
```

---

## Schema: `applications` (Lifecycle)

---

### `applications`

Core application record.

```sql
CREATE TYPE application_stage AS ENUM (
    'discovered', 'eligibility_review', 'loi_drafting', 'loi_submitted',
    'invited_to_apply', 'application_drafting', 'internal_review',
    'board_review', 'submitted', 'pending_decision',
    'awarded', 'declined', 'waitlisted', 'withdrawn', 'closed'
);

CREATE TABLE applications (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID NOT NULL REFERENCES organizations(id),
    grant_id                UUID NOT NULL REFERENCES grants(id),
    grant_cycle_id          UUID REFERENCES grant_cycles(id),
    
    stage                   application_stage NOT NULL DEFAULT 'discovered',
    title                   TEXT,            -- internal name for this application
    
    -- Request details
    amount_requested        NUMERIC(10,2),
    project_title           TEXT,            -- for project grants
    project_description     TEXT,
    project_start_date      DATE,
    project_end_date        DATE,
    
    -- Outcome
    amount_awarded          NUMERIC(10,2),
    award_date              DATE,
    decline_reason          TEXT,
    
    -- Submission
    submitted_at            TIMESTAMPTZ,
    submission_confirmation TEXT,            -- portal confirmation number / email ref
    portal_username         TEXT,            -- encrypted; funder portal login
    portal_password_ref     TEXT,            -- reference to Secrets Manager entry (never store plaintext)
    
    -- Team
    assignee_id             UUID REFERENCES users(id),
    reviewer_id             UUID REFERENCES users(id),
    board_reviewer_id       UUID REFERENCES board_members(id),
    
    -- LOI
    loi_submitted_at        TIMESTAMPTZ,
    loi_outcome             TEXT,            -- 'invited' | 'declined' | 'pending'
    
    notes                   TEXT,
    internal_priority       SMALLINT,        -- 1-5
    
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ
);

CREATE INDEX idx_applications_org_id ON applications (org_id);
CREATE INDEX idx_applications_grant_id ON applications (grant_id);
CREATE INDEX idx_applications_stage ON applications (org_id, stage);
CREATE INDEX idx_applications_assignee ON applications (assignee_id);
```

---

### `application_stage_history`

Audit trail of stage transitions.

```sql
CREATE TABLE application_stage_history (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    from_stage      application_stage,
    to_stage        application_stage NOT NULL,
    changed_by      UUID REFERENCES users(id),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_app_stage_history_application ON application_stage_history (application_id);
```

---

### `application_sections`

Narrative sections for a specific application. One row per required section.

```sql
CREATE TABLE application_sections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    section_name        TEXT NOT NULL,       -- e.g. "Organizational History"
    section_key         TEXT NOT NULL,       -- e.g. "org_history" (stable identifier)
    word_limit          INTEGER,
    char_limit          INTEGER,
    current_content     TEXT,
    word_count          INTEGER,
    char_count          INTEGER,
    compliance_score    SMALLINT,            -- 0-100 from compliance checker
    compliance_issues   JSONB,               -- [{element, severity, message}]
    is_complete         BOOLEAN NOT NULL DEFAULT FALSE,
    is_locked           BOOLEAN NOT NULL DEFAULT FALSE,  -- locked after submission
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (application_id, section_key)
);

CREATE INDEX idx_application_sections_application ON application_sections (application_id);
```

---

### `application_section_versions`

Version history for each section.

```sql
CREATE TABLE application_section_versions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    section_id      UUID NOT NULL REFERENCES application_sections(id) ON DELETE CASCADE,
    version_number  INTEGER NOT NULL,
    content         TEXT NOT NULL,
    word_count      INTEGER,
    char_count      INTEGER,
    created_by      UUID REFERENCES users(id),
    generation_meta JSONB,    -- {model, prompt_hash, atoms_used: [uuid,...], generation_ms}
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_section_versions_section ON application_section_versions (section_id, version_number);
```

---

### `application_comments`

```sql
CREATE TABLE application_comments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    section_id      UUID REFERENCES application_sections(id),
    user_id         UUID NOT NULL REFERENCES users(id),
    content         TEXT NOT NULL,
    resolved        BOOLEAN NOT NULL DEFAULT FALSE,
    parent_id       UUID REFERENCES application_comments(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_application_comments_application ON application_comments (application_id);
```

---

### `application_tasks`

Checklist items and tasks within an application workspace.

```sql
CREATE TYPE task_type AS ENUM ('checklist_document', 'action', 'approval');

CREATE TABLE application_tasks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    task_type       task_type NOT NULL DEFAULT 'action',
    title           TEXT NOT NULL,
    description     TEXT,
    assignee_id     UUID REFERENCES users(id),
    due_date        DATE,
    is_complete     BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,
    completed_by    UUID REFERENCES users(id),
    sort_order      SMALLINT NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_application_tasks_application ON application_tasks (application_id);
```

---

### `application_documents`

Links between applications and documents.

```sql
CREATE TABLE application_documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id  UUID NOT NULL REFERENCES applications(id) ON DELETE CASCADE,
    document_id     UUID NOT NULL REFERENCES documents(id),
    attachment_role TEXT,    -- e.g. "IRS 990", "Audit", "Work Sample"
    is_required     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (application_id, document_id)
);
```

---

### `deadlines`

Unified deadline registry for calendar and alert system.

```sql
CREATE TYPE deadline_type AS ENUM (
    'loi', 'application', 'reporting_interim', 'reporting_final', 'stewardship', 'other'
);

CREATE TABLE deadlines (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    application_id  UUID REFERENCES applications(id),
    award_id        UUID REFERENCES awards(id),
    deadline_type   deadline_type NOT NULL,
    title           TEXT NOT NULL,
    due_date        DATE NOT NULL,
    due_time        TIME,
    timezone        TEXT NOT NULL DEFAULT 'America/New_York',
    notes           TEXT,
    is_complete     BOOLEAN NOT NULL DEFAULT FALSE,
    completed_at    TIMESTAMPTZ,
    alert_sent_60d  BOOLEAN NOT NULL DEFAULT FALSE,
    alert_sent_30d  BOOLEAN NOT NULL DEFAULT FALSE,
    alert_sent_14d  BOOLEAN NOT NULL DEFAULT FALSE,
    alert_sent_7d   BOOLEAN NOT NULL DEFAULT FALSE,
    alert_sent_2d   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_deadlines_org_due ON deadlines (org_id, due_date) WHERE is_complete = FALSE;
CREATE INDEX idx_deadlines_alert_scan ON deadlines (due_date) WHERE is_complete = FALSE;
```

---

## Schema: `awards` (Post-Award)

```sql
CREATE TABLE awards (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id      UUID NOT NULL REFERENCES applications(id),
    org_id              UUID NOT NULL REFERENCES organizations(id),
    grant_id            UUID NOT NULL REFERENCES grants(id),
    award_amount        NUMERIC(10,2) NOT NULL,
    grant_period_start  DATE NOT NULL,
    grant_period_end    DATE NOT NULL,
    agreement_s3_key    TEXT,
    conditions          JSONB,       -- [{condition, is_met, notes}]
    reporting_schedule  JSONB,       -- [{type: 'interim'|'final', due_date, submitted_at}]
    restrictions        TEXT,
    notes               TEXT,
    is_closed           BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_awards_org_id ON awards (org_id);
CREATE INDEX idx_awards_application ON awards (application_id);
```

---

### `award_expenditures`

```sql
CREATE TABLE award_expenditures (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id        UUID NOT NULL REFERENCES awards(id) ON DELETE CASCADE,
    budget_line     TEXT NOT NULL,
    description     TEXT,
    amount          NUMERIC(10,2) NOT NULL,
    expense_date    DATE NOT NULL,
    vendor          TEXT,
    document_id     UUID REFERENCES documents(id),    -- receipt or invoice
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_award_expenditures_award ON award_expenditures (award_id);
```

---

### `award_impact_data`

```sql
CREATE TABLE award_impact_data (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id                    UUID NOT NULL REFERENCES awards(id) ON DELETE CASCADE,
    reporting_period_start      DATE,
    reporting_period_end        DATE,
    performances_count          SMALLINT,
    attendance_total            INTEGER,
    participants_served         INTEGER,
    education_programs_count    SMALLINT,
    education_participants      INTEGER,
    custom_metrics              JSONB,     -- funder-specific metrics
    narrative_outcomes          TEXT,
    created_by                  UUID REFERENCES users(id),
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_award_impact_award ON award_impact_data (award_id);
```

---

### `stewardship_log`

```sql
CREATE TABLE stewardship_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    award_id        UUID NOT NULL REFERENCES awards(id),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    funder_id       UUID NOT NULL REFERENCES funders(id),
    activity_type   TEXT NOT NULL,    -- 'thank_you_letter' | 'performance_invitation' | 'update_email' | 'site_visit' | 'call'
    description     TEXT,
    contact_id      UUID REFERENCES funder_contacts(id),
    occurred_at     DATE NOT NULL,
    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_stewardship_award ON stewardship_log (award_id);
CREATE INDEX idx_stewardship_funder ON stewardship_log (funder_id);
```

---

## Schema: `ai` (AI Engine)

---

### `narrative_atoms`

Parsed and chunked text segments from org documents, available for RAG retrieval.

```sql
CREATE TABLE narrative_atoms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    document_id     UUID REFERENCES documents(id) ON DELETE CASCADE,
    source_type     TEXT NOT NULL,   -- 'prior_application' | 'org_profile' | 'program_desc' | 'bio'
    section_type    TEXT,            -- 'org_history' | 'project_description' | 'evaluation_plan' | etc.
    content         TEXT NOT NULL,
    word_count      INTEGER,
    chunk_index     INTEGER,         -- position within source document
    embedding       VECTOR(3072),    -- text-embedding-3-large
    metadata        JSONB,           -- {fiscal_year, grant_name, funder_name, section_name}
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_narrative_atoms_org_id ON narrative_atoms (org_id);
CREATE INDEX idx_narrative_atoms_source_type ON narrative_atoms (org_id, source_type);
-- HNSW index for approximate nearest neighbor vector search
CREATE INDEX idx_narrative_atoms_embedding ON narrative_atoms USING hnsw (embedding vector_cosine_ops);
```

---

### `generation_jobs`

Tracks AI generation requests and their status.

```sql
CREATE TYPE job_status AS ENUM ('queued', 'processing', 'complete', 'failed');

CREATE TABLE generation_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID NOT NULL REFERENCES organizations(id),
    application_id  UUID REFERENCES applications(id),
    section_id      UUID REFERENCES application_sections(id),
    job_type        TEXT NOT NULL,    -- 'generate_section' | 'generate_full' | 'generate_report'
    status          job_status NOT NULL DEFAULT 'queued',
    requested_by    UUID REFERENCES users(id),
    celery_task_id  TEXT,
    input_meta      JSONB,            -- {grant_id, section_key, emphasis, word_limit}
    output_meta     JSONB,            -- {model, tokens_used, atoms_retrieved, generation_ms}
    error_message   TEXT,
    queued_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_generation_jobs_application ON generation_jobs (application_id);
CREATE INDEX idx_generation_jobs_status ON generation_jobs (status) WHERE status IN ('queued', 'processing');
```

---

## Schema: `discovery` (Grant Discovery)

---

### `discovery_queue`

Newly discovered or changed grants awaiting staff review.

```sql
CREATE TYPE discovery_status AS ENUM ('pending', 'approved', 'rejected', 'duplicate');

CREATE TABLE discovery_queue (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    grant_id            UUID REFERENCES grants(id),    -- null if brand new
    funder_id           UUID REFERENCES funders(id),
    source              TEXT NOT NULL,                 -- 'grants_gov' | 'candid' | 'scraper'
    source_url          TEXT,
    source_external_id  TEXT,
    raw_data            JSONB,
    relevance_score     NUMERIC(4,3),                  -- 0.000 to 1.000
    eligibility_result  JSONB,                         -- {eligible: bool, reasons: []}
    change_summary      TEXT,                          -- for existing grants with changes
    is_new_grant        BOOLEAN NOT NULL DEFAULT TRUE,
    status              discovery_status NOT NULL DEFAULT 'pending',
    reviewed_by         UUID REFERENCES users(id),
    reviewed_at         TIMESTAMPTZ,
    review_notes        TEXT,
    discovered_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_discovery_queue_status ON discovery_queue (status) WHERE status = 'pending';
CREATE INDEX idx_discovery_queue_source ON discovery_queue (source);
```

---

### `scraper_runs`

Log of each scraper execution.

```sql
CREATE TABLE scraper_runs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    funder_id           UUID REFERENCES funders(id),
    source              TEXT NOT NULL,
    status              TEXT NOT NULL,    -- 'success' | 'partial' | 'failed'
    grants_found        INTEGER NOT NULL DEFAULT 0,
    grants_changed      INTEGER NOT NULL DEFAULT 0,
    grants_new          INTEGER NOT NULL DEFAULT 0,
    error_message       TEXT,
    started_at          TIMESTAMPTZ NOT NULL,
    completed_at        TIMESTAMPTZ,
    duration_seconds    INTEGER
);

CREATE INDEX idx_scraper_runs_funder ON scraper_runs (funder_id);
CREATE INDEX idx_scraper_runs_started ON scraper_runs (started_at DESC);
```

---

## Schema: `auth` (Users & Access)

---

### `users`

```sql
CREATE TYPE user_role AS ENUM (
    'admin', 'staff', 'artistic_director', 'board_member', 'read_only'
);

CREATE TABLE users (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID NOT NULL REFERENCES organizations(id),
    email                   TEXT NOT NULL,
    hashed_password         TEXT,
    role                    user_role NOT NULL DEFAULT 'staff',
    first_name              TEXT,
    last_name               TEXT,
    avatar_url              TEXT,
    is_active               BOOLEAN NOT NULL DEFAULT TRUE,
    is_email_verified       BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_enabled             BOOLEAN NOT NULL DEFAULT FALSE,
    mfa_secret_ref          TEXT,         -- reference to Secrets Manager
    last_login_at           TIMESTAMPTZ,
    invited_by              UUID REFERENCES users(id),
    invitation_token_hash   TEXT,         -- hashed; cleared after acceptance
    invitation_expires_at   TIMESTAMPTZ,
    notification_prefs      JSONB NOT NULL DEFAULT '{}',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ,

    UNIQUE (org_id, email)
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_org ON users (org_id);
```

---

### `audit_log`

Immutable audit trail for all security-relevant events.

```sql
CREATE TABLE audit_log (
    id              BIGSERIAL PRIMARY KEY,
    org_id          UUID REFERENCES organizations(id),
    user_id         UUID REFERENCES users(id),
    action          TEXT NOT NULL,           -- e.g. 'application.stage_changed', 'user.invited'
    resource_type   TEXT,
    resource_id     UUID,
    old_value       JSONB,
    new_value       JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_log_org ON audit_log (org_id, created_at DESC);
CREATE INDEX idx_audit_log_user ON audit_log (user_id, created_at DESC);
CREATE INDEX idx_audit_log_resource ON audit_log (resource_type, resource_id);
```

---

## Row-Level Security (RLS)

RLS ensures no organization can access another's data, even via direct database queries. Applied to all tenant-scoped tables.

```sql
-- Example: Enable RLS on applications
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;

CREATE POLICY applications_org_isolation ON applications
    USING (org_id = current_setting('app.current_org_id')::uuid);

-- Set at session start (done by connection pool per-request)
-- SET app.current_org_id = '<org_uuid>';
```

The same pattern is applied to: `org_profiles`, `org_financials`, `board_members`, `staff_members`, `concert_seasons`, `documents`, `grant_watchlist`, `applications`, `application_sections`, `application_comments`, `application_tasks`, `deadlines`, `awards`, `award_expenditures`, `award_impact_data`, `stewardship_log`, `narrative_atoms`, `generation_jobs`, `users`.

---

*Last Updated: 2026-05-01*
