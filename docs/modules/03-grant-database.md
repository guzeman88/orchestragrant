# Module 03 — Grant Database

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Purpose

The Grant Database is the living encyclopedia of every grant opportunity the organization can apply for. It is the knowledge layer that replaces years of accumulated institutional research. It is pre-seeded with ≥ 200 fully populated records at launch and continuously updated via the Discovery Pipeline.

---

## 2. Data Architecture

See [Database Schema](../data/database-schema.md) for full DDL. Key tables:
- `funders` — The grantmaking organization
- `grants` — The specific grant program
- `grant_cycles` — A specific application cycle instance
- `funder_contacts` — Program officers and key contacts

---

## 3. Seed Database — Launch Content

The seed database is loaded at initial deployment and covers all major performing arts funding sources. Each record is fully populated before launch (no partial entries).

### 3.1 Federal Programs (18 records at launch)

| Grant | Funder | Type | Award Range | Cycle |
|---|---|---|---|---|
| Art Works | National Endowment for the Arts | Project / GOS | $10K–$100K | Annual |
| Challenge America | National Endowment for the Arts | Project | $10K | Annual |
| Our Town | National Endowment for the Arts | Community | $25K–$150K | Annual |
| Research: Art Works | National Endowment for the Arts | Research | $10K–$30K | Annual |
| Public Programs in the Humanities | National Endowment for the Humanities | Project | $25K–$300K | Annual |
| Humanities Connections | National Endowment for the Humanities | Education | $30K–$100K | Annual |
| Museums for America | IMLS | Project | $25K–$250K | Annual |
| National Leadership Grants | IMLS | Capacity | $100K–$500K | Annual |
| CCAP (AmeriCorps arts) | AmeriCorps | Capacity | Varies | Annual |
| HUD CDBG Arts | HUD (pass-through states) | Community | Varies | Varies |

*Note: 8 additional federal records from specialized CFDA codes are included in full seed data.*

### 3.2 State Arts Councils (56 records at launch)

One record per state/territory arts council. Each record includes:
- General operating support program
- Project support program
- Touring program (where applicable)
- Education program (where applicable)

All 56 state arts councils are populated. Priority fully populated states (org's home state + 5 largest granting states):
- Illinois Arts Council Agency
- California Arts Council
- New York State Council on the Arts
- Texas Commission on the Arts
- Florida Division of Arts and Culture
- Pennsylvania Council on the Arts

### 3.3 Performing Arts Foundations (60+ records at launch)

Fully populated records for all foundations listed in the PRD's discovery source list, plus:

| Foundation | Key Programs |
|---|---|
| League of American Orchestras | Orchestra Innovation Fund, Catalyst Fund |
| Chamber Music America | Classical Commissioning, Residency |
| New Music USA | Project Grants, Amplifying Voices |
| Aaron Copland Fund | Recording Program, Performance Program |
| Fromm Music Foundation | Commissions |
| Barlow Endowment | Commissions |
| Presser Foundation | Advancement of Music, Special Projects |
| Amphion Foundation | General support for chamber and orchestral music |
| ASCAP Foundation | Morton Gould Young Composer Awards + Grants |
| BMI Foundation | Grants to composers + orchestras |
| American Music Center | Various |
| Foundation for Contemporary Arts | Emergency Grants |
| Koussevitzky Foundation | Commissions |
| Serge Koussevitzky Music Foundation | Commissions |
| Alice M. Ditson Fund | American music programming |
| Meet the Composer (MTC/NMU legacy) | Incorporated into NMU |
| Ann and Gordon Getty Foundation | Music programs |
| Gluck Fellows Program | N/A |

### 3.4 Major Private Foundations (40+ records at launch)

Mellon, Knight, MacArthur, Ford, Pew, Kresge, Doris Duke, Surdna, Bloomberg, Barr, Irvine, Rockefeller Brothers, Carnegie Corporation — with all currently active grant programs for arts organizations populated.

### 3.5 Community Foundations (20 records at launch)

Top 20 community foundations by asset size, covering major metropolitan markets where small orchestras are most concentrated.

---

## 4. Grant Record Completeness Standard

Every grant record in the database must meet the following completeness standard before being marked `verified`:

| Field Group | Required Fields |
|---|---|
| Identity | name, funder_id, grant_type, guidelines_url OR guidelines_s3_key |
| Eligibility | eligible_org_types, geographic_restriction |
| Award | award_min OR award_max, grant_type |
| Application | application_format, at least 1 required_section entry |
| Cycle | cycle_type, application_deadline_typical OR a grant_cycle record |
| Verification | last_verified_at within 90 days |

Records not meeting the standard display a "Needs Verification" badge.

---

## 5. Funder Intelligence Profiles

Each funder has a rich profile page beyond the basic database record. The profile is maintained by the platform team and includes:

- **Giving philosophy** — Narrative description of what the funder cares about
- **Historical priorities** — How their giving focus has evolved
- **Known grantees** — Peer orchestras/ensembles they have funded (from 990 data)
- **What they fund** — Bulleted list of program types
- **What they don't fund** — Explicit exclusions
- **Application process notes** — Tips from the field ("Program officers prefer calls before applying," "LOIs should be no longer than 2 pages despite the 3-page guideline")
- **Program officer notes** — Current program officers (name, email, role) and any contextual notes
- **News** — Curated news items about the funder
- **990 data** — Total giving, top grantees, grants to arts organizations

---

## 6. Grant Record Lifecycle

```
DISCOVERED (auto or manual)
    │
    ▼
PENDING REVIEW (in discovery queue)
    │
    ├─ Staff reviews: Approve / Reject
    │
    ▼ (approved)
DRAFT (in database, not yet complete)
    │
    ▼
VERIFIED (all required fields populated, manually confirmed)
    │
    ├─ Scraper monitors for changes → triggers NEEDS_REVIEW flag
    │
    ├─ Staff re-verifies after change → returns to VERIFIED
    │
    └─ Grant cycle ends and no new cycle → UNDER_REVIEW for dead grant check
```

---

## 7. Grant Search & Discovery Features

### 7.1 Search Capabilities

- **Full-text search:** Against grant name, funder name, and description using PostgreSQL `tsvector`
- **Semantic search:** Vector similarity search against grant descriptions for concept-level matching (e.g., search "community music" finds grants mentioning "underserved audiences" and "music access")
- **Filter by:**
  - Grant type (multi-select)
  - Funder type (multi-select)
  - Award range (range slider)
  - Geographic eligibility (national / state / city)
  - LOI required (toggle)
  - Match required (toggle)
  - Show only eligible grants (toggle — applies pre-screener)
  - Last verified within N days
- **Sort by:** Relevance, deadline, award amount (asc/desc), recently added

### 7.2 Eligibility Overlay

When "Show only eligible" is toggled, the grant list is pre-filtered using the org's profile:
- Geography, budget range, org type, mission focus, membership requirements
- Ineligible grants are hidden; grants requiring manual review are shown with a badge

### 7.3 Application History Overlay

For each grant in the list, the system overlays the org's own application history:
- "Applied 3 times — Last awarded: 2023 ($22,000)"
- "Never applied — Similar orgs awarded: 12 in last cycle"

---

## 8. Grant Record Versioning

When grant guidelines change materially, the previous version is archived. The grant record maintains:
- `last_verified_at` — when a human last confirmed the current data
- `guidelines_s3_key` — path to the most recent archived PDF snapshot
- Historical snapshots in S3 at `grant-archives/{grant_id}/{YYYY-MM-DD}.pdf`

Staff can access previous versions from the grant record detail page.

---

## 9. Manual Grant Entry

Staff can manually add a grant not yet in the database:

1. Enter funder name — system checks for existing funder record, creates if not found
2. Fill grant fields via a structured form (same fields as the database schema)
3. Upload guidelines PDF
4. Grant is created in DRAFT status
5. Staff verifies and marks as VERIFIED

Manual entries go into the org's private grant database section. The platform team reviews them monthly for promotion to the shared database.

---

## 10. Grant Database Maintenance Workflow

The platform has an internal admin dashboard for the database maintenance team:

- **Verification queue** — All grants with `last_verified_at` > 60 days
- **Change detection queue** — Grants flagged by scraper as changed
- **Dead grant queue** — Grants with no cycle in > 18 months
- **New addition queue** — Grants approved from discovery but not yet fully populated

SLA for the database team:
- Verification cycle: all records re-verified within 90 days
- Change flagged records: reviewed within 5 business days
- Dead grant review: completed within 14 business days

---

*Last Updated: 2026-05-01*
