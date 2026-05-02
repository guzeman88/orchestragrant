# OrchestraGrant Platform — Documentation Index

## Project Overview

OrchestraGrant is an AI-powered grant intelligence and application management platform purpose-built for per-service and small performing arts organizations. It replaces the function of a full development consulting firm by discovering every applicable grant, maintaining a living database of funder requirements, managing the complete application lifecycle, and generating publication-quality narratives from existing organizational materials.

---

## Document Index

### 1. Product

| Document | Description |
|---|---|
| [Product Requirements Document](product/PRD.md) | Authoritative requirements, personas, success metrics, constraints |
| [User Stories](product/user-stories.md) | Full user story backlog by persona and epic |

### 2. Architecture

| Document | Description |
|---|---|
| [System Architecture](architecture/system-architecture.md) | High-level system design, component diagram, data flow |
| [Tech Stack](architecture/tech-stack.md) | Technology choices with rationale for each layer |
| [Security Specification](architecture/security-spec.md) | Auth, authorization, data protection, compliance |

### 3. Data

| Document | Description |
|---|---|
| [Database Schema](data/database-schema.md) | Full PostgreSQL DDL for all tables, indexes, constraints |
| [Data Models](data/data-models.md) | Application-layer TypeScript interfaces and Zod schemas |

### 4. API

| Document | Description |
|---|---|
| [API Reference](api/api-reference.md) | All REST endpoints, request/response shapes, auth requirements |
| [Integration Specifications](api/integration-specs.md) | Third-party API integrations, webhooks, OAuth flows |

### 5. AI & ML

| Document | Description |
|---|---|
| [AI Engine Design](ai/ai-engine-design.md) | RAG architecture, LLM integration, writing engine pipeline |
| [Grant Discovery Pipeline](ai/grant-discovery-pipeline.md) | Web scraping, classifier, change detection, relevance scoring |

### 6. Frontend

| Document | Description |
|---|---|
| [Frontend Architecture](frontend/frontend-architecture.md) | Next.js structure, state management, routing, component design |
| [Component Library](frontend/component-library.md) | Core UI components, design tokens, patterns |

### 7. Module Specifications

| Document | Description |
|---|---|
| [Module 01 — Org Intelligence Hub](modules/01-org-intelligence.md) | Org profile, asset library, document vault |
| [Module 02 — Grant Discovery Engine](modules/02-grant-discovery.md) | Automated discovery, scraping, eligibility pre-screening |
| [Module 03 — Grant Database](modules/03-grant-database.md) | Grant records, funder profiles, maintenance workflows |
| [Module 04 — AI Writing Engine](modules/04-ai-writing-engine.md) | Narrative generation, atom library, quality controls |
| [Module 05 — Application Lifecycle](modules/05-application-lifecycle.md) | Pipeline management, workspaces, deadlines, submissions |
| [Module 06 — Post-Award & Compliance](modules/06-post-award.md) | Agreements, expenditure tracking, reporting |
| [Module 07 — Analytics & Strategy](modules/07-analytics.md) | Win rates, forecasting, benchmarking, gap analysis |
| [Module 08 — Knowledge Base](modules/08-knowledge-base.md) | Style guide, training content, reference library |

### 8. DevOps & Infrastructure

| Document | Description |
|---|---|
| [Infrastructure & Deployment](devops/infrastructure.md) | Cloud architecture, containerization, CI/CD, environments |

### 9. Testing

| Document | Description |
|---|---|
| [Testing Strategy](testing/testing-strategy.md) | Unit, integration, E2E, AI evaluation, performance testing |

---

## Glossary of Key Terms

| Term | Definition |
|---|---|
| **Per-service orchestra** | An ensemble that employs musicians on a per-performance contract basis rather than full-time salaried positions |
| **Grant atom / Narrative atom** | A discrete, reusable paragraph or passage extracted from prior applications or org documents |
| **Funder** | The grantmaking organization (foundation, government agency, corporation) |
| **Application** | A specific submission to a specific funder for a specific grant cycle |
| **LOI** | Letter of Inquiry — a pre-application stage some funders require before inviting a full proposal |
| **Grant cycle** | A funder's recurring application window (annual, biannual, rolling, etc.) |
| **General operating support (GOS)** | Unrestricted grant funds that support overall organizational operations |
| **Project support** | Restricted grant funds tied to a specific program or project |
| **RAG** | Retrieval-Augmented Generation — AI generation grounded in retrieved organizational documents |
| **990** | IRS Form 990, the annual informational return filed by nonprofits, publicly available |

---

## Repository Structure

```
/
├── docs/                   # This documentation
├── apps/
│   ├── web/                # Next.js frontend application
│   └── api/                # FastAPI backend service
├── packages/
│   ├── ai-engine/          # AI writing and analysis engine
│   ├── grant-discovery/    # Scraping and discovery pipeline
│   ├── database/           # Prisma schema and migrations
│   └── shared/             # Shared TypeScript types and utilities
├── infrastructure/
│   ├── terraform/          # Cloud infrastructure as code
│   └── docker/             # Container configurations
└── scripts/                # Seed data, migration scripts, utilities
```

---

## Contributing to Documentation

- All documents use GitHub Flavored Markdown
- Code blocks specify the language for syntax highlighting
- SQL schema blocks use `sql` language tag
- TypeScript type blocks use `typescript` language tag
- Every document includes a **Last Updated** footer
- Breaking changes to any specification require a version bump in that document's header

---

*Last Updated: 2026-05-01*
