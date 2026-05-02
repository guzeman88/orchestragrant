# Product Requirements Document (PRD)

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Status:** Approved for Development  
**Last Updated:** 2026-05-01

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Goals & Success Metrics](#3-goals--success-metrics)
4. [User Personas](#4-user-personas)
5. [Scope & Phasing](#5-scope--phasing)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [Constraints & Assumptions](#8-constraints--assumptions)
9. [Out of Scope](#9-out-of-scope)
10. [Dependencies](#10-dependencies)
11. [Risks](#11-risks)

---

## 1. Executive Summary

OrchestraGrant is a full-stack, AI-powered grant intelligence and application management platform built specifically for per-service and small performing arts organizations. The platform consolidates the functions of a development director, grant researcher, grant writer, and compliance officer into a single, intelligent tool.

The platform ingests an organization's existing documents, builds a comprehensive profile, continuously discovers and maintains a database of applicable grant opportunities, and generates publication-quality grant narratives tailored to each funder's requirements — all while managing the full application lifecycle from discovery through final reporting.

---

## 2. Problem Statement

### Current State

Per-service orchestras and small performing arts organizations face a structural disadvantage in grant fundraising:

- **Staffing gap:** Most cannot afford a full-time development director, let alone a department. Grant writing is absorbed by executive directors or artistic directors who have no specialized training in development.
- **Research burden:** Discovering every applicable grant opportunity requires expertise in federal programs, state arts councils, private foundations, and corporate giving — knowledge that takes years to accumulate.
- **Institutional memory loss:** When staff turns over, grant writing knowledge, funder relationships, and application history are lost.
- **Format fragmentation:** Each funder requires a different format, word count, narrative structure, and attachment set. Adapting materials manually for each application is extremely time-consuming.
- **Compliance risk:** Post-award reporting requirements are complex. Missing a reporting deadline can jeopardize future funding from that funder.
- **Competitive disadvantage:** Large organizations with full development departments submit more applications, submit higher-quality applications, and maintain ongoing funder relationships that small organizations cannot replicate.

### Target User's Current Workflow

1. Search online periodically for grants
2. Maintain a spreadsheet of grants found
3. Write each application from scratch or copy-paste from prior applications manually
4. Track deadlines in a calendar with no system integration
5. Store documents in a mix of email, Google Drive, and physical files
6. Miss reporting deadlines due to lack of system

### Desired Future State

A single platform where an organization's development function is systematically supported: discovery is automated, funder intelligence is always current, narrative generation is AI-assisted and grounded in the org's real story, and no deadline or compliance obligation is ever missed.

---

## 3. Goals & Success Metrics

### Primary Goals

| Goal | Metric | Target |
|---|---|---|
| Increase number of grant applications submitted per year | Applications submitted per org per year | 3x baseline in first year |
| Improve application quality | Award rate | ≥ 40% of submitted applications result in award or shortlist |
| Eliminate missed deadlines | Reporting deadlines missed per year | 0 |
| Reduce time to produce a grant application | Hours from start to submission-ready draft | ≤ 4 hours for standard application |
| Comprehensive grant database coverage | Grants in database relevant to performing arts | ≥ 800 on launch; 95% coverage of NEA, state arts councils, top 500 private foundations |
| System reliability | Uptime | 99.9% |

### Secondary Goals

- Reduce executive director time spent on grant writing by ≥ 60%
- Surface at least 10 new grant opportunities per organization per quarter that the org had not previously identified
- Generate grant revenue forecasting accurate to within ±15%

---

## 4. User Personas

### Persona 1 — The Executive Director (Primary User)

**Name:** Maria  
**Role:** Executive Director, per-service orchestra of 45 musicians  
**Technical proficiency:** Moderate  
**Grant experience:** Self-taught, has submitted 15–20 applications over career  

**Goals:**
- Find every possible grant the orchestra qualifies for
- Produce strong applications without hiring a full-time development person
- Know the status of all applications at a glance
- Never miss a reporting deadline

**Pain points:**
- Spends 20+ hours per week on grant-related tasks during busy periods
- Doesn't know if she's missing grants she should be applying for
- Re-writes the same information in different formats for every funder
- Loses track of which version of an application she submitted

**Key workflows:** Grant discovery, application drafting, deadline management, reporting

---

### Persona 2 — The Part-Time Development Coordinator (Secondary User)

**Name:** James  
**Role:** Part-time Development Coordinator, contracted 20 hours/week  
**Technical proficiency:** High  
**Grant experience:** 3 years, focused on arts sector  

**Goals:**
- Manage a high volume of applications efficiently
- Have all funder intelligence at his fingertips without having to research from scratch
- Collaborate with the ED and board on application review
- Track win rates to optimize grant strategy

**Pain points:**
- Maintains a separate research file for every funder
- Has to manually update grant guidelines each cycle
- Cannot easily delegate application review to the ED
- No system for tracking how grant dollars were spent post-award

**Key workflows:** Application pipeline management, AI writing review, analytics dashboard, post-award compliance

---

### Persona 3 — The Board Treasurer (Tertiary User)

**Name:** Patricia  
**Role:** Board Treasurer  
**Technical proficiency:** Low to moderate  
**Grant experience:** None specific to grant writing  

**Goals:**
- Review and approve applications before submission
- Understand the organization's grant revenue position
- Sign off on budget sections and financial attachments

**Pain points:**
- Gets applications via email with no version control
- Has no visibility into grant pipeline or pending revenue
- Cannot easily review only the sections relevant to her

**Key workflows:** Read-only application review, financial dashboard, approval workflow

---

### Persona 4 — The Grant Consultant (Power User, Phase 6)

**Name:** David  
**Role:** Independent grant consultant managing 8 client organizations  
**Technical proficiency:** High  
**Grant experience:** 15 years, specialist in performing arts  

**Goals:**
- Manage multiple client organizations from one account
- Apply his knowledge of funders across all clients
- Customize AI generation per client's voice and priorities
- Generate reports for clients on portfolio performance

**Key workflows:** Multi-org management, client portfolio dashboard, voice customization, bulk application processing

---

## 5. Scope & Phasing

### Phase 1 — Foundation (MVP)

The minimum viable platform that delivers core value.

**Included:**
- Organization profile and asset library
- Document vault with file upload and management
- Manual grant database entry and curated seed database (top 200 performing arts grants, fully populated on launch)
- Application pipeline management (Kanban + list view)
- Deadline calendar with email alerts
- Basic AI narrative generation from uploaded prior applications
- User authentication, roles, and permissions
- Previous application ingestion and parsing

**Definition of Done for Phase 1:** A development coordinator can manage all active applications, receive deadline alerts, and generate a first draft of a grant application in under 4 hours using only Phase 1 features.

---

### Phase 2 — Grant Intelligence

**Included:**
- Automated grant discovery engine (Grants.gov API + Candid API + web scraper infrastructure)
- Eligibility pre-screening against org profile
- Funder profile pages with rich intelligence
- Automated change detection on known grants
- New grant alert notifications
- Grant relevance scoring

---

### Phase 3 — AI Writing Engine (Full)

**Included:**
- Full RAG-based narrative generation pipeline
- Narrative atom library with semantic search
- Grant guideline compliance checker
- AI suggestion panel in editor
- Tone and emphasis routing by funder type
- Version control on all narrative drafts
- Work sample selector from media library
- Budget narrative generation

---

### Phase 4 — Analytics & Strategy

**Included:**
- Win rate analytics by funder type, grant type, amount range, season
- Grant revenue forecasting
- Funder concentration and diversification analysis
- Peer benchmarking via 990 public data
- Optimal application calendar recommendations

---

### Phase 5 — Post-Award & Compliance

**Included:**
- Grant agreement storage and parsing
- Condition and restriction tracking
- Expenditure tracking per grant
- Impact data collection forms
- AI-assisted report generation
- Multi-grant financial reconciliation ledger
- Stewardship tracking log

---

### Phase 6 — Scale & Ecosystem

**Included:**
- Multi-organization support (consultant mode)
- Collaborative grant applications with partner orgs
- Mobile app (iOS + Android) for approvals and alerts
- Open API for integration with Tessitura, PatronManager, ArtsVision
- Grant consultant marketplace

---

## 6. Functional Requirements

### 6.1 Authentication & Authorization

| ID | Requirement | Priority |
|---|---|---|
| AUTH-01 | Users authenticate via email/password with MFA option | Must Have |
| AUTH-02 | System supports SSO via Google Workspace and Microsoft 365 | Should Have |
| AUTH-03 | Role-based access: Admin, Staff, Artistic Director, Board Member, Read-Only | Must Have |
| AUTH-04 | Each role has a defined permission set governing create/read/update/delete per resource type | Must Have |
| AUTH-05 | Admin can invite users by email; invitation link expires in 72 hours | Must Have |
| AUTH-06 | Session tokens expire after 8 hours of inactivity | Must Have |
| AUTH-07 | All auth events are written to audit log | Must Have |

---

### 6.2 Organization Profile

| ID | Requirement | Priority |
|---|---|---|
| ORG-01 | Organization has a structured profile record with all fields defined in Module 01 spec | Must Have |
| ORG-02 | All profile fields support rich text where noted | Must Have |
| ORG-03 | Profile stores multiple versions of mission/vision statements (short/medium/long) | Must Have |
| ORG-04 | Financial data is stored per fiscal year; system maintains history | Must Have |
| ORG-05 | Profile completeness score (0–100%) is calculated and displayed | Should Have |
| ORG-06 | Profile changes are logged with timestamp and user | Must Have |
| ORG-07 | Profile data is used as context source for all AI generation | Must Have |

---

### 6.3 Document Vault

| ID | Requirement | Priority |
|---|---|---|
| DOC-01 | Support upload of PDF, DOCX, DOC, TXT, XLSX, JPG, PNG, MP3, MP4, WAV | Must Have |
| DOC-02 | Documents are tagged by type (990, audit, application, budget, letter of support, media, other) | Must Have |
| DOC-03 | Documents are versioned; prior versions are retained and accessible | Must Have |
| DOC-04 | Text-extractable documents are parsed and indexed for semantic search | Must Have |
| DOC-05 | System displays a document preview for PDF and image files | Should Have |
| DOC-06 | Documents can be linked to specific grants, applications, and funders | Must Have |
| DOC-07 | Documents can be organized into folders | Should Have |
| DOC-08 | Storage quota is tracked and displayed | Must Have |

---

### 6.4 Grant Database

| ID | Requirement | Priority |
|---|---|---|
| GRANT-01 | System ships with a seed database of ≥ 200 fully populated performing arts grants | Must Have |
| GRANT-02 | Each grant record stores all fields defined in Module 03 spec | Must Have |
| GRANT-03 | Grant records support manual creation, editing, and deletion by Admin and Staff roles | Must Have |
| GRANT-04 | Grant records display a freshness indicator (last verified date) | Must Have |
| GRANT-05 | Grant records link to their source URL and a saved PDF snapshot of guidelines | Must Have |
| GRANT-06 | Funder records are separate from grant records; one funder may have many grants | Must Have |
| GRANT-07 | Grant search supports full-text, tag-based, and filter-based queries | Must Have |
| GRANT-08 | Grant records store application history for this organization | Must Have |
| GRANT-09 | Grant records display estimated competitiveness rating | Should Have |

---

### 6.5 Grant Discovery

| ID | Requirement | Priority |
|---|---|---|
| DISC-01 | System polls Grants.gov API daily for new performing arts opportunities | Must Have |
| DISC-02 | System polls Candid Foundation Directory API weekly for foundation updates | Must Have |
| DISC-03 | Scraper visits all configured funder websites on defined schedule | Must Have |
| DISC-04 | NLP classifier scores each discovered opportunity for performing arts relevance | Must Have |
| DISC-05 | Eligibility pre-screener filters discovered grants against org profile | Must Have |
| DISC-06 | New grants above relevance threshold trigger in-app notification and email alert | Must Have |
| DISC-07 | Change detection compares current vs. cached grant guidelines; alerts on material changes | Must Have |
| DISC-08 | Dead grant detection flags grants with no new cycle in > 18 months | Should Have |
| DISC-09 | Discovery queue is visible to Admin/Staff with ability to review, approve, reject each item | Must Have |

---

### 6.6 Application Pipeline

| ID | Requirement | Priority |
|---|---|---|
| PIPE-01 | Applications exist in defined pipeline stages from Discovered to Closed | Must Have |
| PIPE-02 | Kanban view displays all active applications by stage | Must Have |
| PIPE-03 | List view with sort and filter by funder, amount, deadline, status, assignee | Must Have |
| PIPE-04 | Each application has a workspace containing all related documents, drafts, notes, tasks | Must Have |
| PIPE-05 | Document checklist is auto-populated from the grant's requirements record | Must Have |
| PIPE-06 | Applications support internal comment threads | Must Have |
| PIPE-07 | Applications have an assignee and a reviewer | Must Have |
| PIPE-08 | Stage transitions require confirmation and optionally a required field check | Must Have |
| PIPE-09 | Submitted applications are locked from editing; amendments require explicit unlock | Must Have |
| PIPE-10 | System records the outcome (awarded amount, declined, withdrawn) on closed applications | Must Have |

---

### 6.7 Deadline Management

| ID | Requirement | Priority |
|---|---|---|
| DL-01 | Master deadline calendar aggregates all application LOI, submission, and reporting deadlines | Must Have |
| DL-02 | Calendar views: month, week, agenda | Must Have |
| DL-03 | Automated email reminders at 60, 30, 14, 7, and 2 days before each deadline | Must Have |
| DL-04 | Reminders are configurable per organization | Should Have |
| DL-05 | Calendar supports export to iCal format | Must Have |
| DL-06 | Calendar supports sync with Google Calendar and Outlook | Should Have |
| DL-07 | Reporting deadlines are auto-created when a grant is marked Awarded | Must Have |

---

### 6.8 AI Writing Engine

| ID | Requirement | Priority |
|---|---|---|
| AI-01 | System parses uploaded prior applications into structured narrative sections | Must Have |
| AI-02 | Parsed sections are stored as narrative atoms in a searchable library | Must Have |
| AI-03 | AI generates a draft for each required grant section on demand | Must Have |
| AI-04 | Generated drafts respect the character/word/page limits specified in the grant record | Must Have |
| AI-05 | AI applies tone routing based on funder type | Must Have |
| AI-06 | Grant guideline compliance checker verifies all required elements are addressed | Must Have |
| AI-07 | Editor displays which source document each generated paragraph was derived from | Should Have |
| AI-08 | Users can regenerate any section with a different angle or emphasis | Must Have |
| AI-09 | All AI generation is grounded in the org's actual documents (no fabrication) | Must Have |
| AI-10 | System flags claims that lack supporting data | Should Have |
| AI-11 | Readability scoring (Flesch-Kincaid grade level) is displayed per section | Should Have |

---

### 6.9 Post-Award & Compliance

| ID | Requirement | Priority |
|---|---|---|
| AWARD-01 | Awarded grants transition to an active grant period with defined start/end dates | Must Have |
| AWARD-02 | Grant agreement documents are stored and key conditions extracted | Must Have |
| AWARD-03 | Expenditure log allows recording of expenses against grant budget lines | Must Have |
| AWARD-04 | Impact data collection forms are populated from grant reporting requirements | Must Have |
| AWARD-05 | System generates a first draft of interim and final reports | Must Have |
| AWARD-06 | Multi-grant ledger prevents double-booking of expenses across grants | Should Have |
| AWARD-07 | Stewardship log records all funder touchpoints during grant period | Should Have |

---

### 6.10 Analytics

| ID | Requirement | Priority |
|---|---|---|
| AN-01 | Dashboard: total pipeline value, applications submitted YTD, awarded YTD, win rate | Must Have |
| AN-02 | Win rate breakdown by funder type, grant type, amount range | Should Have |
| AN-03 | Grant revenue forecast with confidence range | Should Have |
| AN-04 | Funder concentration chart (% of total grant revenue per funder) | Should Have |
| AN-05 | Peer benchmarking using Candid/990 data for comparable organizations | Nice to Have |
| AN-06 | Application ROI: estimated staff hours per dollar awarded | Nice to Have |

---

## 7. Non-Functional Requirements

### 7.1 Performance

| Requirement | Target |
|---|---|
| Page load time (95th percentile) | < 2 seconds |
| AI narrative generation time (per section) | < 30 seconds |
| Search results returned | < 500 ms |
| Grant discovery pipeline run time (full crawl) | < 4 hours |
| File upload (up to 50 MB) | < 10 seconds |

### 7.2 Reliability

| Requirement | Target |
|---|---|
| Platform uptime | 99.9% (< 8.7 hours downtime/year) |
| Data backup frequency | Daily with 30-day retention |
| Recovery Point Objective (RPO) | 24 hours |
| Recovery Time Objective (RTO) | 4 hours |

### 7.3 Scalability

- System must support 500 concurrent users without degradation
- Grant database must support ≥ 10,000 grant records
- Document vault must support ≥ 50 GB per organization
- Background job queue must handle ≥ 100 concurrent scraping/AI jobs

### 7.4 Accessibility

- WCAG 2.1 AA compliance for all user-facing pages
- Keyboard navigation support throughout
- Screen reader compatible (ARIA labels, semantic HTML)

### 7.5 Internationalization

- Phase 1: English only
- Phase 6: Spanish language support for grant applications targeting Hispanic/Latino funders

---

## 8. Constraints & Assumptions

### Constraints

- AI generation must be grounded in org-provided documents. The system must never generate factual claims (attendance numbers, financial figures, program counts) that are not derived from uploaded sources.
- Funder portal credentials must be stored with encryption at rest. The system must not transmit credentials in plaintext.
- Grant guideline PDFs must be archived locally. The system cannot rely solely on external URLs that may change or become unavailable.
- The system must comply with CCPA and applicable state privacy laws regarding any personal data of program officers or contacts stored in the system.

### Assumptions

- The organization has an active 501(c)(3) determination letter
- The organization can provide at least 2 prior grant applications for initial AI training/context
- At least one user has Admin role access with authority to configure the org profile
- Organization will maintain the accuracy of its profile data; the system is not responsible for outdated org-provided information

---

## 9. Out of Scope

The following are explicitly not included in any current phase:

- Direct integration with grant funder portals for automated submission (legal and TOS risk; submission is always a manual act)
- Payroll or full accounting system replacement (integration with QuickBooks/Xero is in scope; full accounting is not)
- Donor/individual giving management (CRM features for individual donors are not included)
- Ticket sales or event management
- Music library or score management
- Payroll processing for per-service musicians
- Legal review or legal compliance advisory (the system generates documents; legal sign-off is the organization's responsibility)

---

## 10. Dependencies

| Dependency | Type | Risk if Unavailable |
|---|---|---|
| OpenAI GPT-4o API (or Anthropic Claude API) | External API | High — AI writing engine non-functional; fallback: degrade to template-based generation |
| Grants.gov API | External API | Medium — federal grants not auto-discovered; fallback: manual entry |
| Candid Foundation Directory API | External API | Medium — foundation intelligence degraded; fallback: manual entry |
| AWS S3 (or compatible) | Cloud Infrastructure | High — document vault non-functional |
| PostgreSQL (AWS RDS) | Cloud Infrastructure | Critical — complete platform outage |
| SendGrid (or similar) | Email delivery | Medium — deadline alerts not sent; fallback: in-app notifications only |
| Stripe | Payment processing | Low — billing only; no user workflow impact |

---

## 11. Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Grant guideline changes not detected by scraper | Medium | High | Schedule scraper runs ≥ 3x/week; program officers are primary source of truth; version-archive all guideline PDFs |
| AI generates factual inaccuracies in applications | Medium | Critical | Strict RAG architecture; source attribution required for all claims; human review required before submission |
| Funder APIs change or revoke access | Low | Medium | Abstract API integrations behind adapter layer; fallback to manual discovery |
| LLM API rate limits during peak usage | Medium | Medium | Request queuing; multiple provider fallback (OpenAI → Anthropic) |
| User data breach | Low | Critical | SOC 2 controls; encryption at rest and in transit; penetration testing before launch |
| Grant database becomes stale | High | High | Automated change detection; community reporting; staff verification workflow |

---

*Last Updated: 2026-05-01*
