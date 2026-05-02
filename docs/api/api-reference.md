# API Reference

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Base URL:** `https://api.orchestragrant.com/v1`  
**Last Updated:** 2026-05-01

---

## Overview

All API responses use JSON. All authenticated endpoints require the `Authorization: Bearer <token>` header. Errors follow [RFC 7807 Problem Details](https://tools.ietf.org/html/rfc7807).

### Authentication

JWT tokens issued by `POST /auth/login`. Tokens are RS256-signed, expire in 8 hours, and encode `user_id`, `org_id`, and `role`.

### Pagination

List endpoints use cursor-based pagination:

```json
{
  "data": [...],
  "pagination": {
    "cursor": "eyJpZCI6IjEyMyJ9",
    "has_more": true,
    "total": 847
  }
}
```

Query params: `?cursor=<token>&limit=25` (max limit: 100)

### Error Response Shape

```json
{
  "type": "https://orchestragrant.com/errors/validation-error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The 'amount_requested' field must be a positive number.",
  "errors": [
    { "field": "amount_requested", "message": "Must be greater than 0" }
  ]
}
```

---

## Auth Endpoints

### `POST /auth/login`

Authenticate a user.

**Request:**
```json
{
  "email": "maria@orchestra.org",
  "password": "••••••••"
}
```

**Response 200:**
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": {
    "id": "uuid",
    "email": "maria@orchestra.org",
    "role": "admin",
    "org_id": "uuid",
    "first_name": "Maria",
    "last_name": "Santos"
  }
}
```

**Errors:** `401 Invalid credentials`, `403 Account inactive`, `423 MFA required`

---

### `POST /auth/logout`

Invalidates the current session token. **Auth required.**

**Response 204:** No content.

---

### `POST /auth/refresh`

Exchange a valid token for a new one before expiry. **Auth required.**

**Response 200:** Same shape as login response.

---

### `POST /auth/mfa/verify`

Verify a TOTP code for MFA-enabled accounts.

**Request:** `{ "totp_code": "123456", "temp_token": "eyJ..." }`  
**Response 200:** Same shape as login response.

---

### `POST /auth/invite`

Invite a new user to the organization. **Auth required. Role: admin.**

**Request:**
```json
{
  "email": "james@orchestra.org",
  "role": "staff",
  "first_name": "James",
  "last_name": "Kim"
}
```

**Response 201:**
```json
{ "id": "uuid", "email": "james@orchestra.org", "role": "staff", "invited_at": "2026-05-01T12:00:00Z" }
```

---

### `POST /auth/accept-invite`

Accept an invitation and set a password.

**Request:** `{ "token": "invite_token", "password": "••••••••" }`  
**Response 200:** Same shape as login response.

---

## Organization Endpoints

### `GET /org`

Get the current user's organization profile. **Auth required.**

**Response 200:**
```json
{
  "id": "uuid",
  "name": "Meridian Chamber Orchestra",
  "legal_name": "Meridian Chamber Orchestra Inc.",
  "ein": "82-1234567",
  "state": "IL",
  "city": "Chicago",
  "website_url": "https://meridianorchestra.org",
  "ensemble_size_min": 35,
  "ensemble_size_max": 55,
  "per_service_model": true,
  "subscription_tier": "professional",
  "profile": {
    "mission_short": "Bringing world-class chamber music to Chicago neighborhoods.",
    "mission_medium": "...",
    "mission_long": "...",
    "dei_statement": "...",
    "community_need_statement": "...",
    "annual_attendance": 8500,
    "annual_participants_served": 3200
  },
  "profile_completeness_score": 78,
  "storage_used_bytes": 2147483648,
  "storage_quota_bytes": 53687091200
}
```

---

### `PATCH /org`

Update organization base fields. **Auth required. Role: admin, staff.**

**Request:** Any subset of updatable org fields.

**Response 200:** Updated org object.

---

### `PATCH /org/profile`

Update the rich narrative org profile. **Auth required. Role: admin, staff.**

**Request:** Any subset of `org_profiles` fields.

**Response 200:** Updated profile object.

---

### `GET /org/financials`

List all fiscal year financial records. **Auth required.**

**Response 200:**
```json
{
  "data": [
    {
      "fiscal_year": 2025,
      "operating_budget": 420000,
      "total_revenue": 385000,
      "total_expenses": 372000,
      "revenue_breakdown": { "earned": 95000, "grants": 220000, "individual": 70000 }
    }
  ]
}
```

---

### `PUT /org/financials/:year`

Create or replace financial data for a fiscal year. **Auth required. Role: admin, staff.**

---

### `GET /org/board-members`

List all board members. **Auth required.**

---

### `POST /org/board-members`

Add a board member. **Auth required. Role: admin, staff.**

**Request:**
```json
{
  "first_name": "Patricia",
  "last_name": "Nguyen",
  "title": "Treasurer",
  "employer": "First National Bank",
  "employer_title": "VP Finance",
  "term_start": "2024-09-01",
  "is_officer": true
}
```

---

### `PUT /org/board-members/:id`

Update a board member record. **Auth required. Role: admin, staff.**

---

### `DELETE /org/board-members/:id`

Soft-delete a board member. **Auth required. Role: admin.**

---

### `GET /org/users`

List all users in the organization. **Auth required. Role: admin.**

---

### `PATCH /org/users/:id`

Update a user's role or status. **Auth required. Role: admin.**

---

## Documents

### `POST /documents/upload-url`

Request a presigned S3 URL for direct client upload. **Auth required.**

**Request:**
```json
{
  "filename": "FY2025_990.pdf",
  "mime_type": "application/pdf",
  "file_size_bytes": 2457600,
  "doc_type": "irs_990",
  "fiscal_year": 2025
}
```

**Response 200:**
```json
{
  "document_id": "uuid",
  "upload_url": "https://s3.amazonaws.com/...",
  "expires_in": 900
}
```

After upload, call `POST /documents/:id/confirm` to trigger indexing.

---

### `POST /documents/:id/confirm`

Signals that client-side S3 upload is complete. Triggers text extraction and embedding job. **Auth required.**

**Response 202:** `{ "job_id": "uuid", "status": "queued" }`

---

### `GET /documents`

List documents. **Auth required.**

**Query params:** `?doc_type=irs_990&fiscal_year=2025&search=audit&limit=25&cursor=...`

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "FY2025_990.pdf",
      "doc_type": "irs_990",
      "status": "indexed",
      "file_size_bytes": 2457600,
      "fiscal_year": 2025,
      "tags": [],
      "created_at": "2026-01-15T10:00:00Z"
    }
  ],
  "pagination": { "cursor": null, "has_more": false, "total": 1 }
}
```

---

### `GET /documents/:id`

Get document metadata and a presigned download URL. **Auth required.**

**Response 200:** Document object + `{ "download_url": "...", "download_url_expires_in": 300 }`

---

### `PATCH /documents/:id`

Update document metadata (name, tags, description, fiscal_year). **Auth required. Role: admin, staff.**

---

### `DELETE /documents/:id`

Soft-delete a document. **Auth required. Role: admin.**

---

## Grants (Database)

### `GET /grants`

Search and filter the grant database. **Auth required.**

**Query params:**
- `search=<text>` — full-text search across name, description
- `grant_type=general_operating`
- `funder_type=private_foundation`
- `state=IL` — eligible in state
- `award_min=5000&award_max=50000`
- `loi_required=false`
- `match_required=false`
- `limit=25&cursor=...`

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Arts Engagement Grant",
      "funder": {
        "id": "uuid",
        "name": "Knight Foundation",
        "funder_type": "private_foundation",
        "logo_url": "..."
      },
      "grant_type": "project",
      "award_min": 10000,
      "award_max": 100000,
      "award_typical": 35000,
      "loi_required": true,
      "match_required_pct": 0,
      "geographic_restriction": "national",
      "next_deadline": "2026-09-15",
      "last_verified_at": "2026-04-01T00:00:00Z",
      "is_on_watchlist": false,
      "org_eligibility": "eligible"
    }
  ],
  "pagination": { "cursor": "...", "has_more": true, "total": 247 }
}
```

---

### `GET /grants/:id`

Get full grant record. **Auth required.**

**Response 200:** Complete grant object with funder, required sections, required attachments, upcoming cycles, and org's application history.

---

### `POST /grants`

Manually create a new grant record. **Auth required. Role: admin, staff.**

---

### `PATCH /grants/:id`

Update a grant record. **Auth required. Role: admin, staff.**

---

### `POST /grants/:id/verify`

Mark a grant record as verified with the current date. **Auth required. Role: admin, staff.**

**Response 200:** `{ "last_verified_at": "2026-05-01T14:00:00Z", "verified_by": "uuid" }`

---

### `POST /grants/:id/watchlist`

Add grant to org watchlist. **Auth required.**  
**DELETE /grants/:id/watchlist** — Remove from watchlist.

---

### `GET /funders`

List funders with filtering. **Auth required.**

**Query params:** `?funder_type=federal&state=IL&search=...`

---

### `GET /funders/:id`

Get full funder profile including all grants and intelligence notes. **Auth required.**

---

## Applications

### `GET /applications`

List all applications. **Auth required.**

**Query params:**
- `stage=application_drafting`
- `assignee_id=uuid`
- `grant_type=general_operating`
- `deadline_before=2026-09-01`
- `sort=deadline_asc` (options: `deadline_asc`, `deadline_desc`, `amount_desc`, `created_desc`)

---

### `POST /applications`

Create a new application. **Auth required. Role: admin, staff.**

**Request:**
```json
{
  "grant_id": "uuid",
  "grant_cycle_id": "uuid",
  "amount_requested": 25000,
  "title": "FY2027 General Operating Support - NEA",
  "assignee_id": "uuid"
}
```

**Response 201:** Application object. Also auto-creates tasks from grant's required attachments checklist and a deadline record.

---

### `GET /applications/:id`

Get full application workspace. **Auth required.**

**Response 200:** Application with sections, tasks, comments, documents, stage history, deadline(s).

---

### `PATCH /applications/:id`

Update application fields. **Auth required. Role: admin, staff.**

---

### `POST /applications/:id/stage`

Advance or revert pipeline stage. **Auth required. Role: admin, staff.**

**Request:** `{ "stage": "internal_review", "notes": "Draft complete, ready for ED review." }`

**Response 200:** Updated application. Emits WebSocket event `application.stage_changed`.

---

### `POST /applications/:id/submit`

Mark application as submitted. Locks all sections. **Auth required. Role: admin, staff.**

**Request:**
```json
{
  "submitted_at": "2026-05-01T14:32:00Z",
  "submission_confirmation": "NEA-2026-12345",
  "notes": "Submitted via Grants.gov portal."
}
```

---

### `POST /applications/:id/outcome`

Record the application outcome. **Auth required. Role: admin, staff.**

**Request:**
```json
{
  "outcome": "awarded",
  "amount_awarded": 20000,
  "award_date": "2026-08-15",
  "notes": "Funded at 80% of requested amount."
}
```

If `outcome = "awarded"`, automatically creates an `award` record and generates reporting deadlines.

---

### Application Sections

#### `GET /applications/:id/sections`

List all sections for an application. **Auth required.**

#### `PATCH /applications/:id/sections/:section_key`

Save edited content to a section. **Auth required. Role: admin, staff.**

**Request:** `{ "content": "..." }` — Automatically computes word/char count. Creates a new version record.

#### `POST /applications/:id/sections/:section_key/generate`

Trigger AI generation for a section. **Auth required. Role: admin, staff.**

**Request:**
```json
{
  "emphasis": "community_impact",
  "additional_context": "Focus on our youth education program for this section.",
  "regenerate": false
}
```

**Response 202:**
```json
{
  "job_id": "uuid",
  "status": "queued",
  "estimated_seconds": 20
}
```

Monitor via WebSocket or `GET /jobs/:id`.

---

### Application Comments

#### `GET /applications/:id/comments`

#### `POST /applications/:id/comments`

**Request:** `{ "content": "This paragraph is too vague. Can we add the attendance figure?", "section_id": "uuid" }`

#### `PATCH /applications/:id/comments/:comment_id`

#### `DELETE /applications/:id/comments/:comment_id`

---

### Application Tasks

#### `GET /applications/:id/tasks`

#### `POST /applications/:id/tasks`

**Request:**
```json
{
  "title": "Upload FY2025 audit",
  "task_type": "checklist_document",
  "assignee_id": "uuid",
  "due_date": "2026-06-01"
}
```

#### `PATCH /applications/:id/tasks/:task_id`

Mark complete, reassign, update due date.

---

## AI Generation

### `GET /jobs/:id`

Check status of an AI generation job. **Auth required.**

**Response 200:**
```json
{
  "id": "uuid",
  "status": "complete",
  "job_type": "generate_section",
  "completed_at": "2026-05-01T14:05:32Z",
  "output_meta": {
    "model": "gpt-4o",
    "tokens_used": 1842,
    "atoms_retrieved": 7,
    "generation_ms": 18240
  }
}
```

---

### `GET /narrative-atoms`

Browse the organization's narrative atom library. **Auth required.**

**Query params:** `?section_type=org_history&search=community+engagement&limit=20`

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "content": "Founded in 2005, the Meridian Chamber Orchestra has grown from...",
      "source_type": "prior_application",
      "section_type": "org_history",
      "metadata": { "fiscal_year": 2024, "funder_name": "Mellon Foundation" },
      "word_count": 87
    }
  ]
}
```

---

## Deadlines & Calendar

### `GET /deadlines`

List deadlines for the organization. **Auth required.**

**Query params:** `?from=2026-05-01&to=2026-08-31&deadline_type=application`

**Response 200:**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "NEA Art Works — Application Deadline",
      "deadline_type": "application",
      "due_date": "2026-07-01",
      "is_complete": false,
      "application": { "id": "uuid", "stage": "application_drafting" }
    }
  ]
}
```

---

### `GET /deadlines/calendar`

Returns deadlines grouped by month for calendar display. **Auth required.**

**Query params:** `?year=2026&month=6`

---

### `GET /deadlines/ical`

Returns iCal format (.ics) of all upcoming deadlines. **Auth required.**  
**Response:** `Content-Type: text/calendar`

---

## Discovery

### `GET /discovery/queue`

List pending discovery queue items for review. **Auth required. Role: admin, staff.**

**Query params:** `?status=pending&source=grants_gov`

---

### `POST /discovery/queue/:id/approve`

Approve a discovered grant (adds to database). **Auth required. Role: admin, staff.**

---

### `POST /discovery/queue/:id/reject`

Reject a discovered grant with a reason. **Auth required. Role: admin, staff.**

**Request:** `{ "reason": "Not applicable — restricts to visual arts only." }`

---

### `GET /discovery/runs`

View scraper run history. **Auth required. Role: admin.**

---

## Awards & Post-Award

### `GET /awards`

List active awards for the organization. **Auth required.**

---

### `GET /awards/:id`

Full award record with expenditures, impact data, and stewardship log. **Auth required.**

---

### `POST /awards/:id/expenditures`

Log a grant expenditure. **Auth required. Role: admin, staff.**

---

### `GET /awards/:id/expenditures`

List expenditures for an award. **Auth required.**

---

### `POST /awards/:id/impact-data`

Submit an impact data collection record. **Auth required. Role: admin, staff.**

---

### `POST /awards/:id/generate-report`

Trigger AI-assisted report generation. **Auth required. Role: admin, staff.**

**Request:** `{ "report_type": "final", "reporting_period_end": "2026-12-31" }`

**Response 202:** Job object.

---

### `POST /awards/:id/stewardship`

Log a stewardship activity. **Auth required. Role: admin, staff.**

**Request:**
```json
{
  "activity_type": "thank_you_letter",
  "description": "Sent personalized thank you letter to Program Officer Jane Smith.",
  "contact_id": "uuid",
  "occurred_at": "2026-05-02"
}
```

---

## Analytics

### `GET /analytics/dashboard`

Returns summary KPIs. **Auth required.**

**Response 200:**
```json
{
  "pipeline_total_value": 485000,
  "applications_submitted_ytd": 18,
  "applications_awarded_ytd": 7,
  "total_awarded_ytd": 142000,
  "win_rate_ytd": 0.389,
  "deadlines_next_30_days": 4,
  "discovery_queue_pending": 12
}
```

---

### `GET /analytics/win-rate`

Win rate breakdown. **Auth required.**

**Query params:** `?breakdown=funder_type&fiscal_year=2025`

---

### `GET /analytics/pipeline`

Pipeline value by stage. **Auth required.**

---

### `GET /analytics/funder-concentration`

Funder concentration chart data. **Auth required.**

---

### `GET /analytics/forecast`

12-month grant revenue forecast. **Auth required.**

---

## WebSocket Events

Connect to: `wss://api.orchestragrant.com/v1/ws?token=<jwt>`

### Events pushed to client:

| Event | Payload | Description |
|---|---|---|
| `generation.complete` | `{ job_id, section_id, content_preview }` | AI section generation finished |
| `generation.failed` | `{ job_id, error }` | AI generation failed |
| `application.stage_changed` | `{ application_id, from_stage, to_stage, changed_by }` | Pipeline stage moved |
| `discovery.new_grants` | `{ count, top_relevance_score }` | New grants found in discovery run |
| `deadline.alert` | `{ deadline_id, title, due_date, days_remaining }` | Deadline alert triggered |
| `document.indexed` | `{ document_id, atom_count }` | Document parsing complete |
| `notification.new` | `{ message, type, link }` | General in-app notification |

---

*Last Updated: 2026-05-01*
