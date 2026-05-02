# Tech Stack

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

Each technology choice below includes the decision rationale and alternatives considered.

---

## Frontend

### Core Framework: Next.js 15 (App Router)

**Rationale:** Next.js provides server-side rendering for SEO and initial load performance, React Server Components for efficient data fetching, and built-in API route support. The App Router simplifies layouts and nested routing for the complex multi-panel UI (pipeline, workspaces, editor side-by-side). Excellent TypeScript support, large ecosystem, and well-understood by most React engineers.

**Alternatives considered:**
- *Vite + React SPA:* Faster dev builds but no SSR; complex workarounds for initial load performance
- *Remix:* Strong data-loading model but smaller ecosystem and fewer available component libraries

### Language: TypeScript 5

**Rationale:** Strong typing across the frontend and shared packages catches entire categories of runtime errors at compile time. Especially valuable for complex data models (grant records, application states) and LLM response schemas. Shared type package with the API layer eliminates type drift.

### State Management: Zustand + TanStack Query

**Rationale:**
- **TanStack Query (React Query):** Handles all server state — fetching, caching, background refresh, optimistic updates for the pipeline Kanban. Eliminates the need for Redux for async server state.
- **Zustand:** Lightweight store for global UI state only (sidebar open/closed, active organization, draft editor state). Avoids Redux boilerplate for simple shared UI state.

**Alternatives considered:**
- *Redux Toolkit:* Overkill for this use case; significant boilerplate for minimal benefit
- *Jotai:* Excellent but team familiarity with Zustand is higher

### Rich Text Editor: Tiptap 2

**Rationale:** Tiptap is built on ProseMirror and provides a fully extensible headless editor. Critical requirements: custom AI suggestion nodes (inline suggestions that can be accepted/rejected), source attribution highlighting, word count per section, custom formatting controls for grant applications. Tiptap's extension model supports all of these. ProseMirror ensures production-grade editing reliability.

**Alternatives considered:**
- *Lexical (Meta):* Newer, faster, but immature extension ecosystem
- *Quill:* Limited extensibility; customizations require forking
- *Slate:* Excellent extensibility but complex to implement reliably for production use

### UI Component Library: shadcn/ui + Radix UI Primitives

**Rationale:** shadcn/ui provides high-quality, accessible, copy-paste components built on Radix primitives. The components are owned by the project (not a black-box npm package) so they can be customized without fighting library constraints. Radix provides unstyled, fully accessible primitives (Dialog, Tooltip, Dropdown, etc.) satisfying WCAG 2.1 AA requirements.

### Styling: Tailwind CSS 4

**Rationale:** Utility-first CSS scales well in a team environment — no naming collisions, no dead CSS, consistent design token application. Tailwind's JIT compilation keeps bundle size minimal. Works seamlessly with shadcn/ui.

### Data Visualization: Recharts

**Rationale:** React-native charting library. Sufficient for the analytics dashboard requirements (bar, line, pie, area charts). Lightweight. Good TypeScript support.

**Alternatives considered:**
- *D3.js:* More powerful but requires much more implementation work for standard chart types
- *Nivo:* Feature-rich but larger bundle size

### Form Management: React Hook Form + Zod

**Rationale:** React Hook Form minimizes re-renders on form input (critical for the large org profile form). Zod provides runtime schema validation that can be shared with the API layer for consistent validation rules.

### Kanban: dnd-kit

**Rationale:** dnd-kit is the modern replacement for react-beautiful-dnd. Accessible (keyboard drag-and-drop), high performance, and maintained. Used for the application pipeline Kanban board.

---

## Backend

### Core Framework: FastAPI (Python 3.12)

**Rationale:** FastAPI is the right choice for an AI-heavy backend:
- Native async support (critical for non-blocking LLM API calls)
- Automatic OpenAPI schema generation from type hints (our API reference auto-generates)
- Pydantic v2 integration for ultra-fast request/response validation
- Python is the de facto language for ML/AI tooling — no language boundary between API and AI services
- Performance (async FastAPI with uvicorn) is comparable to Node.js for I/O-bound workloads

**Alternatives considered:**
- *Node.js/Express or Hono:* Strong for pure API work but adds a language boundary with Python AI services; AI libraries are a first-class Python ecosystem
- *Django REST Framework:* Mature but synchronous by default; ORM is heavier than needed

### ORM: SQLAlchemy 2 + Alembic

**Rationale:** SQLAlchemy 2 has full async support via `asyncpg`. Alembic for database migrations (industry standard pairing with SQLAlchemy). Provides fine-grained control over queries — important for the complex grant search and analytics queries.

**Alternatives considered:**
- *Prisma (via Prisma Client Python):* Better DX for simple CRUD but limited for complex queries; ecosystem primarily JavaScript-oriented
- *Tortoise ORM:* Less mature

### Background Jobs: Celery 5 + Redis

**Rationale:** Celery is the most battle-tested Python task queue. Required features: scheduled periodic tasks (scraper runs), task routing to specific queues (scraping vs. AI generation), retry with exponential backoff, task result storage, monitoring via Flower. Redis as broker is fast and already in our stack for caching.

**Alternatives considered:**
- *RQ (Redis Queue):* Simpler but lacks Celery's scheduling, routing, and monitoring
- *Dramatiq:* Modern alternative but smaller ecosystem and fewer team members with experience

### WebSockets: FastAPI WebSocket + Redis Pub/Sub

**Rationale:** AI generation can take 10–30 seconds. WebSocket push notifications replace polling: when a generation job completes, the AI service publishes to Redis pub/sub; the Main API WebSocket server relays the message to the connected client. FastAPI's built-in WebSocket support is sufficient.

### Authentication: FastAPI-Users + PyJWT

**Rationale:** FastAPI-Users provides pre-built user registration, login, and password reset flows. JWT tokens (RS256) for stateless authentication — private key in AWS Secrets Manager. FastAPI dependency injection makes auth middleware clean and testable.

---

## Database Layer

### Primary Database: PostgreSQL 16

**Rationale:** PostgreSQL is the clear choice:
- JSONB columns for flexible schema sections (grant requirements vary significantly)
- Full-text search via `tsvector` for the grant database search (supplemented by pgvector for semantic)
- `pgvector` extension runs in the same cluster — no separate vector DB to manage in Phase 1
- Row-level security (RLS) for multi-organization data isolation
- Excellent AWS RDS managed service support

**Version:** 16 (pgvector support, logical replication improvements)

### Vector Database: pgvector (PostgreSQL extension)

**Rationale:** pgvector runs as a PostgreSQL extension, eliminating operational overhead of a separate vector database service. At our scale (< 10M vectors), pgvector with HNSW indexing provides sufficient performance. If we scale beyond ~50M vectors, migrate to a dedicated service (Pinecone or Weaviate).

### Cache & Job Queue: Redis 7

**Rationale:** Redis serves two roles:
1. Application cache (session data, frequently read grant records, analytics aggregates)
2. Celery message broker (job queues)

Using Redis for both reduces operational complexity. Redis Cluster mode for high availability.

### Object Storage: AWS S3

**Rationale:** S3 is the industry standard for document storage. All uploaded documents, media files, grant PDF archives, and exported reports stored in S3. Versioning enabled. Lifecycle rules tier old grant PDFs to S3 Glacier after 2 years.

---

## AI & ML Layer

### LLM Provider: OpenAI GPT-4o (primary) + Anthropic Claude 3.5 Sonnet (fallback)

**Rationale:** GPT-4o provides the best balance of quality, speed, and cost for long-form grant narrative generation. Anthropic Claude 3.5 Sonnet is configured as a fallback — both models are accessed through an abstraction layer so switching is seamless. The abstraction also allows per-use-case model selection (lighter model for compliance checking, premium model for full application generation).

**Provider abstraction:** All LLM calls go through an internal `LLMClient` class that handles provider selection, retry, rate limiting, and cost tracking.

### Embedding Model: OpenAI text-embedding-3-large

**Rationale:** Highest-quality OpenAI embedding model. 3072-dimensional vectors. Used for all narrative atom embeddings and semantic search. Cost is acceptable given embedding is done once per document chunk, not per generation.

### Document Parsing: LlamaParse (cloud) + pdfplumber (local fallback)

**Rationale:** LlamaParse (LlamaIndex cloud service) provides superior PDF parsing — handles multi-column layouts, tables, scanned PDFs via OCR, and complex grant guideline formatting. Falls back to pdfplumber for plain PDFs when LlamaParse is unavailable or for cost optimization on simple documents.

**For Word documents:** python-docx

### Web Scraping: Playwright (Python)

**Rationale:** Playwright handles JavaScript-rendered pages (many funder websites use React/Angular). Supports multiple browsers (Chromium, Firefox, WebKit). Can handle cookie consent banners and basic bot detection. Runs headless in Docker.

**Rotating proxies:** Bright Data residential proxies for sites with aggressive bot protection.

**Alternatives considered:**
- *Scrapy:* Excellent for simple HTML but poor JavaScript support
- *Selenium:* Older, slower, heavier

### NLP Classifier: Zero-shot classification via LLM

**Rationale:** Rather than training a custom classifier (requires labeled dataset), we use an LLM (GPT-4o-mini, cost-optimized) with a structured prompt to classify grant relevance. This is flexible — the classification criteria can be updated in a prompt without retraining. If performance or cost becomes an issue, migrate to a fine-tuned BERT-based classifier.

---

## Infrastructure & DevOps

### Container Platform: Docker + AWS ECS Fargate

**Rationale:** Fargate eliminates EC2 instance management. Each service runs in its own Docker container with independently scalable task counts. Fargate Spot for non-critical workers reduces cost by up to 70%.

### Infrastructure as Code: Terraform

**Rationale:** Terraform supports all required AWS resources. Team has existing Terraform experience. State stored in S3 with DynamoDB locking.

### CI/CD: GitHub Actions

**Rationale:** Integrated with the GitHub monorepo. Workflow: PR → lint + test → build Docker image → push to ECR → deploy to staging → integration test → manual approval → deploy to production.

### Monitoring: CloudWatch + Grafana Cloud

**Rationale:** CloudWatch for native AWS metrics and log aggregation. Grafana Cloud for unified dashboards combining CloudWatch, custom application metrics (via Prometheus remote write), and business KPI dashboards.

### Secret Management: AWS Secrets Manager

**Rationale:** All API keys (OpenAI, Candid, Grants.gov, SendGrid, Stripe), database credentials, and JWT private keys stored in Secrets Manager. Automatic rotation for database credentials. Accessed by services via IAM role — no hardcoded secrets anywhere.

---

## Communication & Email

### Transactional Email: AWS SES

**Rationale:** Cost-effective ($0.10/1000 emails), high deliverability, native AWS integration. Used for: deadline reminders, application notifications, board approval requests, new grant alerts, user invitations.

**Email templates:** React Email (JSX-based templates that render to HTML + plain text) compiled to static HTML stored in S3.

### Internal Notifications (Phase 6): Slack API

**Rationale:** Slack is the most common team communication tool. Webhook-based integration for pipeline event notifications and alerts.

---

## Payments & Billing

### Payment Processing: Stripe

**Rationale:** Industry standard. Subscription billing for SaaS plans. Stripe Billing handles proration, trial periods, and invoice generation automatically.

---

## Development Tooling

| Tool | Purpose |
|---|---|
| pnpm workspaces | Monorepo package management (frontend + shared packages) |
| uv (Python package manager) | Python dependency management for all backend services |
| ESLint + Prettier | Frontend linting and formatting |
| Ruff + Black | Python linting and formatting |
| Pytest | Python unit and integration testing |
| Vitest | Frontend unit testing |
| Playwright (test mode) | E2E browser testing |
| Docker Compose | Local development environment |
| pre-commit | Git hook enforcement of linting/formatting |
| Conventional Commits | Commit message format for automated changelog |
| Sentry | Error tracking (frontend + backend) |

---

*Last Updated: 2026-05-01*
