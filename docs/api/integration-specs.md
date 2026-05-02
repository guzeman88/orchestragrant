# Integration Specifications

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Overview

OrchestraGrant integrates with external services for grant data, AI generation, financial synchronization, communication, and billing. This document specifies each integration: purpose, credentials, data flow, error handling, and fallback behavior.

---

## 2. Grants.gov API

**Purpose:** Real-time discovery of federal grant opportunities  
**Documentation:** https://www.grants.gov/web/grants/developers.html  
**Auth:** API Key (stored in AWS Secrets Manager as `grants-gov/api-key`)

### Data Flow

```
Celery task: poll_grants_gov (daily 02:00 UTC)
    │
    ├─ POST /v2/opportunities/search
    │   Filters: eligibilities=["nonprofits"], fundingCategories=["AR","ED"]
    │   Pages through results (max 100 per page)
    │
    ├─ For each opportunity:
    │   ├─ GET /v2/opportunities/{opportunityId} (full record)
    │   └─ Check if opportunityId exists in grants.external_id
    │       ├─ New: dispatch to classifier
    │       └─ Existing: compare modifiedDate → dispatch to change detector
    │
    └─ Write to discovery_queue if new or changed
```

### Key Fields Mapped

| Grants.gov Field | OrchestraGrant Field |
|---|---|
| `opportunityTitle` | `grants.name` |
| `synopsis.synopsisDesc` | `grants.description` |
| `synopsis.applicantTypes` | `grants.eligible_org_types` |
| `synopsis.awardCeiling` | `grants.award_max` |
| `synopsis.awardFloor` | `grants.award_min` |
| `synopsis.closeDate` | `grant_cycles.application_deadline` |
| `opportunityNumber` | `grants.external_id` |
| `agencyName` | Used to match/create `funders` record |

### Error Handling

- HTTP 429 (rate limit): back off 60 seconds, retry up to 3 times
- HTTP 5xx: log error, skip cycle, alert engineering via Slack
- Network timeout (> 30s): retry once, then mark scraper_run as failed

### Fallback

If Grants.gov API is unavailable for > 24 hours: send alert to staff that federal grant discovery is paused; no automated fallback (manual check recommended).

---

## 3. Candid Foundation Directory API

**Purpose:** Foundation profiles, grant history, 990 data for funder intelligence  
**Documentation:** https://candid.org/find-funding/foundation-directory  
**Auth:** OAuth 2.0 Client Credentials (client_id + client_secret in Secrets Manager)

### Integration Points

**3.1 Foundation Profile Enrichment**

When a new funder is added to the database (manually or via discovery):
```python
async def enrich_funder_from_candid(funder: Funder):
    # Search by name or EIN
    org = await candid_client.search_organizations(
        name=funder.name,
        ein=funder.ein
    )
    
    if org:
        funder.candid_org_id = org.id
        funder.total_giving_annual = org.total_giving
        funder.last_990_year = org.last_990_year
        funder.priorities = org.giving_interests
        
        # Fetch top grantees for intelligence notes
        grantees = await candid_client.get_grants(
            funder_id=org.id,
            recipient_type="organization",
            limit=20
        )
        # Store for peer benchmarking
        await store_peer_grant_data(funder.id, grantees)
```

**3.2 Peer Benchmarking (Analytics Module)**

Weekly job: fetch 990 grant data for comparable orchestras (filtered by NTEE code A69 — Symphony & Chamber Music) to populate peer benchmarking charts.

**3.3 New Foundation Discovery**

Monthly job: search Candid for new foundations with:
- Giving areas including "performing arts" or "music"
- Minimum giving: $50,000/year
- US-based
- 990 data available (public filer)

New foundations dispatched to discovery pipeline for classification and review.

### Error Handling

- API unavailable: log and skip; weekly cadence means missing one cycle is acceptable
- Rate limit (1000 requests/day): queue requests across the day; prioritize funder enrichment over discovery

---

## 4. OpenAI API

**Purpose:** LLM-based narrative generation, document classification, compliance checking  
**Model:** `gpt-4o` (generation), `gpt-4o-mini` (classification, compliance checks)  
**Embeddings:** `text-embedding-3-large`  
**Auth:** API Key in Secrets Manager as `openai/api-key`

### Request Configuration

```python
OPENAI_DEFAULTS = {
    "generation": {
        "model": "gpt-4o",
        "temperature": 0.4,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
        "timeout": 120,         # seconds
    },
    "classification": {
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "max_tokens": 512,
        "response_format": {"type": "json_object"},
        "timeout": 30,
    },
    "embedding": {
        "model": "text-embedding-3-large",
        "dimensions": 3072,
        "timeout": 30,
    }
}
```

### Rate Limit Management

- Organization-level: OpenAI Tier 4 account; 10M TPM limit
- Application-level: LLMClient implements token bucket rate limiter per org (configurable)
- Request queuing: all generation requests queued via Celery; max 20 concurrent OpenAI requests
- Backpressure: if queue depth > 50, new generation requests are returned with `{ "status": "queued", "estimated_wait_seconds": N }` and client polls or listens via WebSocket

### Cost Tracking

```python
async def log_llm_usage(job_id: str, usage: CompletionUsage, model: str):
    cost = calculate_cost(
        input_tokens=usage.prompt_tokens,
        output_tokens=usage.completion_tokens,
        model=model
    )
    
    await db.execute("""
        UPDATE generation_jobs 
        SET output_meta = output_meta || $1::jsonb
        WHERE id = $2
    """, json.dumps({
        "tokens_input": usage.prompt_tokens,
        "tokens_output": usage.completion_tokens,
        "cost_usd": cost,
        "model": model
    }), job_id)
    
    await increment_org_monthly_cost(org_id, cost)
```

### Fallback to Anthropic

```python
class LLMClient:
    async def generate(self, **kwargs) -> GenerationResult:
        providers = [
            (self._call_openai, "openai"),
            (self._call_anthropic, "anthropic"),
        ]
        
        for call_fn, provider_name in providers:
            try:
                return await call_fn(**kwargs)
            except (RateLimitError, ServiceUnavailableError) as e:
                logger.warning(f"{provider_name} unavailable: {e}. Trying next.")
                continue
        
        raise AllProvidersFailedError()
```

---

## 5. Anthropic Claude API

**Purpose:** Fallback LLM provider when OpenAI is unavailable  
**Model:** `claude-3-5-sonnet-20241022`  
**Auth:** API Key in Secrets Manager as `anthropic/api-key`

The Anthropic integration uses the same `LLMClient` abstraction. Prompt templates are adapted for Claude's message format (no system-level JSON mode; tool_use used for structured output).

---

## 6. LlamaParse (LlamaIndex Cloud)

**Purpose:** High-quality PDF and document parsing for the document ingestion pipeline  
**Auth:** API Key in Secrets Manager as `llamaparse/api-key`

### Integration Flow

```python
async def parse_document_with_llamaparse(s3_key: str) -> ParsedDocument:
    # Download from S3
    file_bytes = await s3.get_object(Bucket=BUCKET, Key=s3_key)["Body"].read()
    
    # Submit to LlamaParse
    async with aiohttp.ClientSession() as session:
        form_data = aioFormData()
        form_data.add_field("file", file_bytes, filename="document.pdf")
        form_data.add_field("result_type", "markdown")  # preserve structure
        form_data.add_field("language", "en")
        
        resp = await session.post(
            "https://api.cloud.llamaindex.ai/api/parsing/upload",
            data=form_data,
            headers={"Authorization": f"Bearer {LLAMAPARSE_KEY}"}
        )
        job = resp.json()
    
    # Poll for completion (typically 10-60 seconds)
    result = await poll_until_complete(job["id"])
    return ParsedDocument(markdown=result["markdown"], pages=result["pages"])
```

**Fallback:** If LlamaParse fails or times out (> 120s), fall back to `pdfplumber` for digital PDFs or log an error for scanned documents.

---

## 7. AWS SES (Email)

**Purpose:** Transactional emails — deadline reminders, notifications, invitations, alerts  
**Auth:** IAM role (no API key; ECS task role has `ses:SendEmail` permission)  
**Sending domain:** `mail.orchestragrant.com` (SPF, DKIM, DMARC configured)

### Email Templates

All templates are built with **React Email** (JSX → HTML + plain text dual format), compiled and stored in S3:

| Template Key | Trigger | Recipients |
|---|---|---|
| `deadline_reminder_60d` | 60 days before deadline | Assignee + Admin |
| `deadline_reminder_30d` | 30 days before deadline | Assignee + Admin |
| `deadline_reminder_14d` | 14 days before deadline | Assignee + Admin |
| `deadline_reminder_7d` | 7 days before deadline | Assignee + Admin + Reviewer |
| `deadline_reminder_2d` | 2 days before deadline | All org users |
| `grant_discovery_alert` | New grants in discovery queue | Admin + Staff |
| `grant_change_alert` | Material change to watched/pipeline grant | Assignee + Admin |
| `board_review_request` | Application moved to board_review stage | Board reviewer |
| `application_outcome` | Outcome recorded | All org users |
| `user_invitation` | New user invited | Invited user |
| `report_deadline_reminder` | Reporting deadline approaching | Admin + Staff |
| `award_notification` | Grant marked as awarded | All org users |

### Bounce and Complaint Handling

- SES bounce/complaint notifications routed to SQS queue
- Hard bounce: immediately mark user email as invalid; display warning in UI
- Spam complaint: suppress future emails to that address; log for review

---

## 8. Stripe

**Purpose:** Subscription billing for SaaS plans  
**Auth:** Secret key in Secrets Manager as `stripe/secret-key`; Publishable key as environment variable  
**Webhook secret:** In Secrets Manager as `stripe/webhook-secret`

### Subscription Plans

| Tier | Price | Features |
|---|---|---|
| Starter | $99/month | 1 org, 5 users, 10 applications/month, 25 GB storage |
| Professional | $249/month | 1 org, unlimited users, unlimited applications, 100 GB storage |
| Enterprise | Custom | Multi-org (consultant mode), custom storage, SLA |

### Integration Flow

**Checkout:**
```python
async def create_checkout_session(org_id: str, price_id: str) -> str:
    customer_id = await get_or_create_stripe_customer(org_id)
    
    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url="https://app.orchestragrant.com/settings/billing?success=true",
        cancel_url="https://app.orchestragrant.com/settings/billing?canceled=true",
        metadata={"org_id": org_id}
    )
    return session.url
```

**Webhook handling:**

```python
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")
    
    event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    
    match event.type:
        case "customer.subscription.created" | "customer.subscription.updated":
            await sync_subscription_status(event.data.object)
        case "customer.subscription.deleted":
            await handle_subscription_cancelled(event.data.object)
        case "invoice.payment_failed":
            await handle_payment_failed(event.data.object)
```

---

## 9. Google Calendar & Outlook Calendar Sync

**Purpose:** Sync OrchestraGrant deadlines to users' personal/org calendars  
**Method:** iCal feed (Phase 1) + Calendar API push (Phase 2)

### iCal Feed (Phase 1)

Endpoint: `GET /deadlines/ical?token=<signed_token>`

- Signed token: HMAC-SHA256 of `user_id + org_id`, expires never (revocable by regenerating)
- Returns `.ics` file with all non-complete deadlines
- Users subscribe to this URL in Google Calendar / Apple Calendar / Outlook

### Google Calendar API (Phase 2)

OAuth 2.0 flow; user grants calendar access. Each deadline is created/updated as a Google Calendar event with:
- Title: `[OrchestraGrant] {deadline title}`
- Description: Application details + link to application workspace
- Reminders: 7 days and 24 hours (calendar-native)
- Calendar: user can select which Google Calendar to add events to

---

## 10. QuickBooks / Xero API (Phase 5)

**Purpose:** Sync grant expenditures and award amounts to/from the org's accounting system  
**Auth:** OAuth 2.0 per organization (each org connects their own account)

### Data Sync (Phase 5)

**From OrchestraGrant → QuickBooks:**
- Award received → create income entry in specified revenue account
- Expenditure logged → create expense entry in specified expense account tagged to grant project

**From QuickBooks → OrchestraGrant:**
- Pull expense transactions tagged to grant tracking codes into expenditure log for reconciliation

Integration is bidirectional but non-destructive: OrchestraGrant never deletes QuickBooks entries.

---

## 11. Sentry

**Purpose:** Error tracking and performance monitoring for frontend and backend  
**Auth:** DSN in environment variables (non-secret; Sentry DSN is frontend-visible by design)

### Configuration

**Frontend (Next.js):**
```typescript
// sentry.client.config.ts
Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NEXT_PUBLIC_ENV,
  tracesSampleRate: 0.1,   // 10% of transactions traced
  replaysOnErrorSampleRate: 1.0,
  beforeSend(event) {
    // Strip PII from error context
    if (event.user) {
      delete event.user.email;
      delete event.user.username;
    }
    return event;
  }
});
```

**Backend (FastAPI):**
```python
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    environment=settings.ENV,
    traces_sample_rate=0.05,
    before_send=strip_pii_from_event,
)
```

PII stripping ensures no grant application content, financial data, or user emails are sent to Sentry.

---

*Last Updated: 2026-05-01*
