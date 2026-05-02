# Grant Discovery Pipeline

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Overview

The Grant Discovery Pipeline is a continuously running background system that identifies new grant opportunities, detects changes to existing grants, and pre-screens all opportunities against the organization's eligibility profile. It replaces the manual research work of a development researcher.

---

## 2. Data Sources & Collection Schedule

### 2.1 Federal Sources

| Source | Method | Schedule | Notes |
|---|---|---|---|
| **Grants.gov** | REST API (CFDA codes: 45.x arts, 84.x education, 14.x community dev) | Daily 02:00 UTC | Largest federal opportunity database |
| **NEA** | Web scraper (arts.gov/grants) | Every 48 hours | Parse grant program pages and deadline calendars |
| **NEH** | Web scraper (neh.gov/grants) | Every 48 hours | Humanities — overlaps with music history/education |
| **IMLS** | API (imls.gov/grants/apply-grant) | Weekly | Library and museum grants; relevant for education partnerships |
| **AmeriCorps** | Web scraper | Weekly | Arts-embedded national service programs |

### 2.2 State Sources

All 56 state and territorial arts councils are monitored. Scraper configuration is maintained per-state in the funder database:

```python
STATE_ARTS_COUNCILS = [
    {"state": "IL", "url": "arts.illinois.gov/grants", "schedule": "48h"},
    {"state": "CA", "url": "arts.ca.gov/grants", "schedule": "48h"},
    # ... all 56 entries
]
```

Additional state sources per org's service area (configured in org profile):
- State humanities councils
- State community foundation pass-throughs
- State economic development arts programs

### 2.3 Private Foundation Sources

**Tier 1 Foundations** (scrape every 48 hours — highest grant volume for orchestras):

| Foundation | URL Pattern |
|---|---|
| Mellon Foundation | mellon.org/grants |
| Knight Foundation | knightfoundation.org/apply |
| MacArthur Foundation | macfound.org/programs |
| Ford Foundation | fordfoundation.org/work/our-grants |
| Pew Charitable Trusts | pewtrusts.org/en/projects |
| Kresge Foundation | kresge.org/opportunities |
| Doris Duke Charitable Foundation | ddcf.org/grants |
| Bloomberg Philanthropies | bloomberg.org/programs |
| Surdna Foundation | surdna.org/grants |
| Aaron Copland Fund for Music | coplandfund.org/grants |
| American Symphony Orchestra League / LOA | americanorchestras.org/grants |
| Chamber Music America | chambermusic.org/grants |
| New Music USA | newmusicusa.org/grants |
| ASCAP Foundation | ascapfoundation.org/grants |
| BMI Foundation | bmifoundation.org |
| Presser Foundation | presserfoundation.org |
| Amphion Foundation | amphionfoundation.org |

**Tier 2 Foundations** (scrape weekly):
- All remaining foundations in the funder database
- Community foundations in org's service area

**Tier 3** (scrape monthly):
- Corporate giving programs
- Smaller regional foundations

### 2.4 Aggregated Sources

| Source | API/Method | Data Type |
|---|---|---|
| **Candid Foundation Directory** | REST API | Foundation profiles, 990 data, grant history |
| **IRS Tax Exempt Org DB** | Bulk download (monthly) | Funder verification, new foundation identification |
| **Foundation Center GrantCraft** | Web scraper | Grant writing guidance updates |

---

## 3. Scraper Architecture

### 3.1 Scraper Stack

```
Scheduler (Celery Beat)
    │
    ├─ Triggers scrape task per funder on schedule
    │
    ▼
Scraper Worker (Celery worker on EC2 Spot)
    │
    ├─ Playwright browser (headless Chromium)
    ├─ Rotating proxy pool (Bright Data residential)
    ├─ Cookie and session management
    │
    ▼
Raw content extraction
    │
    ├─ HTML text extraction (BeautifulSoup)
    ├─ PDF detection and download → S3 archive
    ├─ Link following (up to depth 3 within funder domain)
    │
    ▼
Content normalization
    │
    ├─ Strip navigation, headers, footers (article extraction heuristic)
    ├─ Deduplicate redundant text
    ├─ Identify grant program blocks
    │
    ▼
Write to raw_scrape_cache (Redis, 7-day TTL)
+ dispatch to classifier and change detector
```

### 3.2 Bot Detection Handling

Many funder websites use basic bot protection. Mitigation strategy:

1. **Respect `robots.txt`** — check before any crawl; do not scrape disallowed paths
2. **Rate limiting** — 1 request per 3 seconds per domain; randomized ±1 second jitter
3. **Rotating residential proxies** — appear as regular user traffic
4. **User agent rotation** — cycle through common browser user agents
5. **Cookie persistence** — maintain session cookies for up to 6 hours
6. **JavaScript rendering** — Playwright executes JavaScript natively (no simple detection bypass needed)
7. **CAPTCHA handling** — if CAPTCHA detected, mark funder as requiring manual check; alert staff

If a funder consistently blocks scraping: switch to manual verification workflow with staff reminder.

### 3.3 Scraper Configuration Schema

Each funder's scraper configuration is stored in the `funders` table under a `scraper_config` JSONB column:

```json
{
  "scraper_type": "playwright",
  "entry_urls": ["https://mellon.org/grants/", "https://mellon.org/grants/arts-and-culture/"],
  "grant_page_patterns": ["/grants/", "/apply/", "/funding/"],
  "pdf_link_patterns": [".pdf", "guidelines", "rfp"],
  "deadline_selectors": [".deadline-date", "[data-deadline]"],
  "pagination": { "type": "load_more", "selector": ".load-more-btn" },
  "rate_limit_delay_ms": 3000,
  "requires_proxy": true,
  "known_captcha": false,
  "last_scrape_status": "success",
  "notes": "Grants page restructured March 2026 — updated selectors"
}
```

---

## 4. Grants.gov API Integration

```python
GRANTS_GOV_BASE = "https://api.grants.gov/v2"

PERFORMING_ARTS_CFDA_PREFIXES = [
    "45.",    # Arts (NEA)
    "45.024", # NEA grants to organizations
    "84.",    # Education (for music education grants)
    "66.",    # EPA (environmental arts programs)
    "93.243", # substance abuse programs with arts components
]

async def poll_grants_gov():
    # Search for newly posted opportunities
    response = await http_client.post(
        f"{GRANTS_GOV_BASE}/opportunities/search",
        json={
            "rows": 100,
            "sortBy": "openDate|desc",
            "filters": {
                "eligibilities": ["nonprofits"],
                "fundingCategories": ["AR", "ED"],  # Arts, Education
                "opportunityStatuses": ["posted"]
            }
        },
        headers={"Authorization": f"Bearer {GRANTS_GOV_API_KEY}"}
    )
    
    opportunities = response.json()["data"]["opportunities"]
    
    for opp in opportunities:
        if is_new_or_changed(opp):
            await dispatch_to_classifier(opp)
```

---

## 5. NLP Relevance Classifier

### 5.1 Classification Task

Input: Grant opportunity text (title + description + eligibility)  
Output: Relevance score (0.0–1.0) for performing arts / orchestral organizations

### 5.2 Implementation

Zero-shot classification via LLM (GPT-4o-mini for cost efficiency):

```python
CLASSIFIER_PROMPT = """
You are classifying grant opportunities for relevance to a per-service symphony orchestra.

The organization:
- Is a 501(c)(3) nonprofit
- Presents classical music concerts (orchestra, chamber music)
- Runs music education programs for youth
- Based in a US city
- Annual budget: $200K–$800K range
- Does NOT have full-time salaried musicians (per-service model)

Grant opportunity:
Title: {title}
Description: {description}
Eligibility: {eligibility}
Funder: {funder_name}

Rate the relevance of this grant for this organization on a scale of 0.0 to 1.0:
- 1.0: Explicitly for orchestras or classical music organizations
- 0.8: For performing arts organizations broadly (includes orchestras)
- 0.6: For arts organizations broadly (includes performing arts)
- 0.4: For nonprofits with arts/culture focus (music could qualify)
- 0.2: For nonprofits generally (arts organizations rarely succeed)
- 0.0: Clearly ineligible (wrong geography, wrong org type, wrong mission)

Return JSON: { "score": <float>, "reasoning": "<one sentence>", "tags": ["<relevant tags>"] }
"""

async def classify_grant(opportunity: dict) -> ClassificationResult:
    result = await llm_client.generate(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": CLASSIFIER_PROMPT.format(**opportunity)
        }],
        temperature=0.0
    )
    return ClassificationResult(**result)
```

**Threshold for discovery queue:** score ≥ 0.60  
**Auto-approve to database (no human review):** score ≥ 0.90 AND funder already in database  
**Human review required:** 0.60 ≤ score < 0.90

---

## 6. Eligibility Pre-Screener

After classification, each opportunity is automatically screened against the organization's profile:

```python
class EligibilityScreener:
    
    def screen(self, grant: Grant, org: Organization) -> EligibilityResult:
        checks = [
            self._check_org_type(grant, org),          # 501(c)(3) required?
            self._check_geography(grant, org),          # Service area match?
            self._check_budget_range(grant, org),       # Budget min/max?
            self._check_years_operation(grant, org),    # Min years required?
            self._check_membership(grant, org),         # Membership required?
            self._check_prior_applicant(grant, org),    # Previous grantee restriction?
            self._check_mission_focus(grant, org),      # Specific mission required?
        ]
        
        failed = [c for c in checks if not c.passed]
        
        return EligibilityResult(
            eligible=len(failed) == 0,
            needs_review=any(c.needs_review for c in checks),
            failed_checks=failed,
            reasons=[c.reason for c in failed]
        )
    
    def _check_geography(self, grant: Grant, org: Organization) -> CheckResult:
        if grant.geographic_restriction == "national":
            return CheckResult(passed=True, reason="National scope")
        
        if grant.geographic_states:
            org_states = org.service_area.get("states", [org.state])
            overlap = set(grant.geographic_states) & set(org_states)
            if overlap:
                return CheckResult(passed=True, reason=f"State match: {overlap}")
            return CheckResult(
                passed=False,
                reason=f"Geographic mismatch: grant requires {grant.geographic_states}, org is in {org.state}"
            )
        
        # City-specific check
        if grant.geographic_cities:
            org_cities = org.service_area.get("cities", [org.city])
            overlap = set(c.lower() for c in grant.geographic_cities) & \
                      set(c.lower() for c in org_cities)
            return CheckResult(
                passed=bool(overlap),
                reason=f"City match: {overlap}" if overlap else "City mismatch"
            )
        
        return CheckResult(passed=True, needs_review=True, reason="Geography unclear — manual review")
```

---

## 7. Change Detection

### 7.1 What Constitutes a Material Change

Not all text differences trigger an alert. Material changes include:

- Application deadline change
- Award amount range change (> 10% difference)
- New or removed required section
- New or removed required attachment
- Eligibility restriction added or removed
- Guidelines URL changed
- Grant program paused or ended

Minor changes (wording clarifications, formatting) are logged but do not trigger user alerts.

### 7.2 Change Detection Process

```python
async def detect_changes(funder_id: str, current_text: str) -> ChangeReport:
    # Fetch cached version from S3 archive
    cached = await s3.get_object(
        Bucket=ARCHIVE_BUCKET,
        Key=f"grant-archives/{funder_id}/latest.txt"
    )
    cached_text = cached["Body"].read().decode("utf-8")
    
    if cached_text == current_text:
        return ChangeReport(has_changes=False)
    
    # Use LLM to identify material changes
    diff_prompt = f"""
    Compare these two versions of grant guidelines and identify MATERIAL changes only.
    
    PREVIOUS VERSION:
    {cached_text[:4000]}
    
    CURRENT VERSION:
    {current_text[:4000]}
    
    Return JSON:
    {{
        "has_material_changes": <bool>,
        "changes": [
            {{
                "type": "deadline" | "amount" | "eligibility" | "section" | "attachment" | "other",
                "description": "<what changed>",
                "previous_value": "<old value if applicable>",
                "new_value": "<new value if applicable>",
                "severity": "high" | "medium" | "low"
            }}
        ]
    }}
    """
    
    result = await llm_client.generate(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": diff_prompt}],
        temperature=0.0
    )
    
    # Archive new version
    await s3.put_object(
        Bucket=ARCHIVE_BUCKET,
        Key=f"grant-archives/{funder_id}/{datetime.utcnow().isoformat()}.txt",
        Body=current_text.encode("utf-8")
    )
    
    return ChangeReport(**result)
```

---

## 8. Dead Grant Detection

Grants that have not had a new cycle in > 18 months are flagged for review:

```python
async def detect_dead_grants():
    stale_grants = await db.fetch("""
        SELECT g.id, g.name, f.name as funder_name,
               MAX(gc.application_deadline) as last_deadline
        FROM grants g
        JOIN funders f ON g.funder_id = f.id
        LEFT JOIN grant_cycles gc ON gc.grant_id = g.id
        WHERE g.is_active = TRUE
        GROUP BY g.id, f.name
        HAVING MAX(gc.application_deadline) < NOW() - INTERVAL '18 months'
           OR MAX(gc.application_deadline) IS NULL
    """)
    
    for grant in stale_grants:
        # Scrape funder website to verify
        current_status = await verify_grant_still_active(grant)
        
        if current_status == "not_found":
            await flag_grant_for_review(grant.id, reason="Not found on funder website")
        elif current_status == "no_current_cycle":
            await flag_grant_for_review(grant.id, reason="No open cycle found in 18+ months")
```

---

## 9. Alert Dispatch

When a new grant or material change is detected:

```python
async def dispatch_discovery_alert(org_id: str, alert: DiscoveryAlert):
    # In-app notification
    await notification_service.create(
        org_id=org_id,
        type="grant_discovery",
        title=alert.title,
        message=alert.message,
        link=f"/discovery/queue/{alert.queue_item_id}",
        priority="high" if alert.relevance_score > 0.85 else "normal"
    )
    
    # Email to Admin and Staff users
    recipients = await get_users_with_notification_pref(
        org_id=org_id,
        pref="email_grant_discovery"
    )
    
    await email_service.send(
        template="grant_discovery_alert",
        recipients=recipients,
        context={
            "grant_name": alert.grant_name,
            "funder_name": alert.funder_name,
            "relevance_score": alert.relevance_score,
            "award_range": alert.award_range,
            "next_deadline": alert.next_deadline,
            "alert_type": alert.type,  # 'new_grant' | 'guidelines_changed' | 'deadline_approaching'
            "review_url": f"https://app.orchestragrant.com/discovery/{alert.queue_item_id}"
        }
    )
```

---

## 10. Discovery Queue Review UI

The staff-facing discovery queue shows:

| Field | Description |
|---|---|
| Grant name + funder | Linked to funder profile |
| Relevance score | Color-coded badge (green ≥ 0.85, yellow 0.70–0.84, orange < 0.70) |
| Eligibility status | Eligible / Needs Review / Ineligible with reason |
| Source | Grants.gov / Candid / [funder website] |
| Discovery date | When the scraper found it |
| Change summary | For existing grants with detected changes |
| Actions | Approve → Add to Database | Reject (with reason) | Add to Watchlist | Start Application |

Staff can bulk-approve multiple items or set a filter to auto-approve all items from trusted sources with score ≥ 0.90.

---

*Last Updated: 2026-05-01*
