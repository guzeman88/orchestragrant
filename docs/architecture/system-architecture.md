# System Architecture

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Architecture Overview

OrchestraGrant is a multi-tier, cloud-native web application built on a microservice-oriented monorepo. The architecture separates concerns across four primary tiers:

1. **Frontend** — Next.js web application (React)
2. **API Layer** — FastAPI (Python) REST API with WebSocket support
3. **AI/ML Services** — Dedicated service cluster for LLM integration, RAG pipeline, and document processing
4. **Data Layer** — PostgreSQL (primary), pgvector (semantic search), Redis (cache/queue), S3 (object storage)

Background processing (grant discovery, scraping, AI generation, email delivery) runs as an async job queue managed by Celery with Redis as the broker.

---

## 2. High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                               │
│                                                                     │
│   ┌──────────────────┐          ┌──────────────────────────────┐   │
│   │  Next.js Web App │          │  Mobile App (Phase 6)        │   │
│   │  (React / TS)    │          │  (React Native)              │   │
│   └────────┬─────────┘          └──────────────┬───────────────┘   │
└────────────┼──────────────────────────────────┼────────────────────┘
             │ HTTPS                             │ HTTPS
             ▼                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (AWS ALB)                       │
│              Rate limiting · TLS termination · Auth token           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────────┐
│   Main API      │  │   AI Service    │  │  Discovery Service   │
│   (FastAPI)     │  │   (FastAPI)     │  │  (FastAPI + Celery)  │
│                 │  │                 │  │                      │
│  - Auth         │  │  - RAG pipeline │  │  - Grant scraper     │
│  - Org profile  │  │  - LLM proxy    │  │  - Grants.gov API    │
│  - Grant DB     │  │  - Doc parsing  │  │  - Candid API        │
│  - Pipeline     │  │  - Atom library │  │  - Change detection  │
│  - Analytics    │  │  - Compliance   │  │  - Classifier        │
│  - Reporting    │  │    checker      │  │  - Alert dispatch    │
└────────┬────────┘  └────────┬────────┘  └──────────┬───────────┘
         │                    │                       │
         └────────────────────┼───────────────────────┘
                              │
              ┌───────────────┼───────────────────────┐
              ▼               ▼                       ▼
    ┌──────────────┐  ┌──────────────────┐  ┌────────────────┐
    │  PostgreSQL  │  │   pgvector DB    │  │     Redis      │
    │  (Primary)   │  │  (Vector Store)  │  │  Cache/Queue   │
    │              │  │                  │  │                │
    │  - All       │  │  - Narrative     │  │  - Session     │
    │    relational│  │    atom embedds  │  │  - Job queue   │
    │    data      │  │  - Grant desc    │  │  - Rate limit  │
    │              │  │    embeddings    │  │  - Pub/sub     │
    └──────────────┘  └──────────────────┘  └────────────────┘

              ┌──────────────────────────────────────┐
              ▼                                      ▼
    ┌──────────────────┐                  ┌──────────────────┐
    │   AWS S3         │                  │  External APIs   │
    │                  │                  │                  │
    │  - Documents     │                  │  - OpenAI/Claude │
    │  - Media files   │                  │  - Grants.gov    │
    │  - Grant PDF     │                  │  - Candid        │
    │    archives      │                  │  - SendGrid      │
    │  - Exports       │                  │  - Stripe        │
    └──────────────────┘                  └──────────────────┘
```

---

## 3. Service Descriptions

### 3.1 Main API Service

**Runtime:** Python 3.12 / FastAPI  
**Deployment:** AWS ECS Fargate (auto-scaling, 2–8 tasks)  
**Responsibilities:**
- All primary business logic: organizations, grants, applications, users, reporting
- Authentication and authorization (JWT issuance and validation)
- File upload coordination (presigned S3 URLs, metadata registration)
- Real-time events via WebSocket (application status changes, notification pushes)
- Webhooks to external services (calendar sync, Slack)

### 3.2 AI Service

**Runtime:** Python 3.12 / FastAPI  
**Deployment:** AWS ECS Fargate with GPU-capable task definition for embedding generation; scales to 0 during idle  
**Responsibilities:**
- Document parsing and text extraction pipeline (LlamaParse, pdfplumber)
- Narrative atom extraction and embedding generation (OpenAI text-embedding-3-large)
- RAG query pipeline: retrieve atoms → construct prompt → call LLM → return structured response
- LLM API proxy with retry, fallback (OpenAI → Anthropic), and rate limit management
- Compliance checker: maps LLM output against grant requirements schema
- Readability and quality scoring

### 3.3 Discovery Service

**Runtime:** Python 3.12 / FastAPI + Celery workers  
**Deployment:** AWS ECS Fargate for API; Celery workers on EC2 Spot instances (cost-optimized for long-running scrape jobs)  
**Responsibilities:**
- Scheduled grant scraping with Playwright (headless Chromium)
- Grants.gov API polling (daily)
- Candid API polling (weekly)
- NLP relevance classifier (fine-tuned BERT or zero-shot via LLM)
- Eligibility pre-screener (rules engine against org profile)
- Change detection (diff of current vs. cached guideline text)
- Dead grant detection (heuristic: no new cycle in > 18 months)
- Alert dispatch to Main API for notification delivery

### 3.4 Background Job Queue

**Broker:** Redis  
**Worker framework:** Celery  
**Job types:**

| Queue | Job Type | Schedule |
|---|---|---|
| `scrape-high` | Per-funder website crawl | Every 48 hours per funder |
| `scrape-federal` | Grants.gov API poll | Daily at 02:00 UTC |
| `scrape-foundation` | Candid API poll | Weekly Sunday 03:00 UTC |
| `change-detection` | Diff known grant guidelines | Every 48 hours |
| `ai-generate` | LLM narrative generation (on-demand) | Triggered by user action |
| `ai-embed` | Document embedding on upload | Triggered by upload event |
| `notifications` | Email/in-app notification dispatch | Triggered by event or schedule |
| `reporting` | Deadline report generation | Daily at 06:00 UTC |

---

## 4. Data Flow Diagrams

### 4.1 Grant Application Generation Flow

```
User clicks "Generate Application"
         │
         ▼
Main API receives request
  - Validates user permissions
  - Fetches grant record (requirements, guidelines, section specs)
  - Fetches org profile
         │
         ▼
Main API dispatches job to ai-generate queue
         │
         ▼
AI Service worker picks up job
  1. Build retrieval context:
     - Semantic search: pgvector query using grant section topic + org name
     - Returns top-k narrative atoms (chunks from prior applications + org profile)
     - Fetches org financial data, program data, board list from PostgreSQL
  
  2. Construct prompt per section:
     - System prompt: funder type tone instructions + section requirements
     - Context: retrieved narrative atoms + org data
     - Instruction: word/character limit + required elements list
  
  3. Call LLM API (OpenAI GPT-4o)
     - Structured output (JSON): section text + source citations
  
  4. Compliance check:
     - Compare generated output against required elements list
     - Return compliance score and missing elements
  
  5. Store draft in PostgreSQL (application_drafts table)
  6. Emit WebSocket event to connected client
         │
         ▼
Frontend receives WebSocket event
  - Renders draft in editor
  - Displays source attributions
  - Displays compliance score
```

### 4.2 Grant Discovery Flow

```
Celery scheduler triggers scrape job (every 48h per funder)
         │
         ▼
Playwright headless browser loads funder grant page
  - Renders JavaScript-heavy pages
  - Extracts text content
  - Checks for PDF links → downloads and archives to S3
         │
         ▼
Change detection:
  - Fetch cached version from Redis/S3
  - Compute text diff
  - If material change detected → flag for review
         │
         ▼
NLP classifier scores content for relevance
  (performing arts / music / orchestral / music education)
  - Score 0.0–1.0
  - If score > 0.65 → eligible for discovery queue
         │
         ▼
Eligibility pre-screener:
  - Geography match: org service area vs. grant geographic restriction
  - Org type match: 501(c)(3) vs. grant eligible types
  - Budget range match: org budget vs. grant min/max
  - Returns: eligible | ineligible | needs-review
         │
         ▼
If new or materially changed:
  - Insert/update grant record in PostgreSQL
  - Push to discovery_queue table
  - Dispatch notification job
         │
         ▼
User sees new grant in Discovery Queue with:
  - Relevance score
  - Eligibility assessment
  - Summary of changes (if existing grant)
```

### 4.3 Document Upload Flow

```
User selects file for upload
         │
         ▼
Frontend requests presigned S3 URL from Main API
  - Main API validates file type, size, user permission
  - Returns presigned URL + document_id
         │
         ▼
Frontend uploads file directly to S3 (presigned URL)
  - Bypasses API for large file performance
  - S3 triggers event on upload complete
         │
         ▼
S3 event → SQS → Main API webhook handler
  - Records document metadata in PostgreSQL
  - Dispatches embedding job to ai-embed queue
         │
         ▼
AI Service embedding worker:
  1. Downloads file from S3
  2. Extracts text (LlamaParse for PDF/Word; direct for TXT)
  3. Chunks text into narrative atoms (512-token chunks with 64-token overlap)
  4. Generates embeddings (OpenAI text-embedding-3-large)
  5. Stores atoms + embeddings in pgvector (narrative_atoms table)
  6. Updates document record: status = "indexed"
         │
         ▼
Document is now searchable and available for RAG generation
```

---

## 5. Deployment Architecture

### 5.1 Cloud Provider

**Primary:** Amazon Web Services (AWS)  
**Regions:** us-east-1 (primary), us-west-2 (disaster recovery)

### 5.2 Infrastructure Components

| Component | AWS Service | Notes |
|---|---|---|
| Compute (API services) | ECS Fargate | Serverless containers; auto-scaling |
| Compute (Celery workers) | EC2 Spot Instances | Cost-optimized for batch jobs |
| Container registry | ECR | Per-service Docker images |
| Load balancer | ALB | Path-based routing to services |
| Primary database | RDS PostgreSQL 16 | Multi-AZ, automated backups |
| Vector database | RDS PostgreSQL 16 + pgvector | Same cluster, separate schema |
| Cache / queue broker | ElastiCache Redis 7 | Cluster mode |
| Object storage | S3 | Versioning enabled; lifecycle rules |
| CDN | CloudFront | Static assets + S3 document delivery |
| DNS | Route 53 | Health-check failover |
| Secrets management | AWS Secrets Manager | All API keys and DB credentials |
| Log aggregation | CloudWatch Logs + OpenSearch | Structured JSON logging |
| Monitoring | CloudWatch + Grafana Cloud | Metrics, dashboards, alerting |
| Email delivery | SES | Transactional + notification emails |
| CI/CD | GitHub Actions + AWS CodeDeploy | See DevOps doc |

### 5.3 Environment Strategy

| Environment | Purpose | Database | AI Calls |
|---|---|---|---|
| `dev` | Local developer machines | Local Docker Compose | Real (with budget cap) |
| `staging` | Pre-release integration testing | Dedicated RDS (smaller instance) | Real (with budget cap) |
| `production` | Live system | RDS Multi-AZ | Real (production keys) |

---

## 6. Security Architecture

See [Security Specification](security-spec.md) for full detail. Summary:

- All inter-service communication over TLS
- JWT-based auth with RS256 signing (private key in Secrets Manager)
- All secrets via AWS Secrets Manager — never in environment variables or source code
- RBAC enforced at API layer, not just frontend
- S3 bucket policy: no public access; all access via presigned URLs or CloudFront signed cookies
- All database connections use IAM authentication (no hardcoded passwords)
- WAF on ALB for OWASP Top 10 protections

---

## 7. Scalability Design

### Stateless Services

All API services are stateless. Session state is stored in Redis. Any ECS task can serve any request.

### Database Connection Pooling

All services connect to PostgreSQL via PgBouncer (connection pooler) deployed as a sidecar. This prevents connection exhaustion under load.

### AI Service Scaling

AI generation is computationally expensive. The AI Service scales to 0 during idle periods. Requests are queued in Redis; the queue depth metric triggers scale-out.

### Grant Discovery Isolation

The discovery service runs in its own compute tier specifically to prevent scraping load (network-heavy, long-running) from affecting API response times.

### Caching Strategy

| Data | Cache | TTL |
|---|---|---|
| Org profile | Redis | 5 minutes |
| Grant record (read) | Redis | 1 hour |
| Funder profile | Redis | 6 hours |
| Discovery queue count | Redis | 30 seconds |
| User session | Redis | 8 hours |
| Analytics aggregates | Redis | 15 minutes |

---

## 8. Observability

### Logging

- Structured JSON logs from all services
- Log levels: DEBUG (dev), INFO (staging/prod), ERROR alerts via CloudWatch Alarm
- Request correlation ID propagated through all service calls
- All AI generation requests logged with input/output hash for audit

### Metrics

- Custom CloudWatch metrics per service: request count, latency p50/p95/p99, error rate, queue depth
- Business metrics: applications created per day, AI generations per day, grants discovered per day
- Grafana dashboards for engineering and product visibility

### Alerting

| Alert | Threshold | Channel |
|---|---|---|
| API error rate | > 1% over 5 minutes | PagerDuty |
| Database CPU | > 80% for 5 minutes | PagerDuty |
| Queue depth (ai-generate) | > 50 jobs | Slack |
| Discovery pipeline failure | Any failure | Slack + email |
| Certificate expiry | 30 days before | Email |

### Distributed Tracing

OpenTelemetry instrumentation on all services. Traces exported to AWS X-Ray. Critical paths traced:
- Grant application generation (end-to-end)
- Document upload and indexing
- Discovery pipeline run

---

*Last Updated: 2026-05-01*
