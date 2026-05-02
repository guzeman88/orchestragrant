# Testing Strategy

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Overview

OrchestraGrant's testing strategy follows the testing pyramid: a large base of fast unit tests, a middle layer of integration tests, and a smaller set of end-to-end tests covering critical user paths. AI generation quality is tested separately via an LLM evaluation framework.

---

## 2. Testing Pyramid

```
          ╔══════════════╗
          ║    E2E       ║  ~50 tests · Playwright
          ║  (~5% of     ║  Critical user paths
          ║  test suite) ║
          ╚══════════════╝
        ╔══════════════════╗
        ║   Integration    ║  ~200 tests · pytest + Vitest
        ║   (~25% of       ║  Service boundaries, DB, APIs
        ║   test suite)    ║
        ╚══════════════════╝
      ╔══════════════════════╗
      ║     Unit Tests       ║  ~750 tests · pytest + Vitest
      ║     (~70% of         ║  Pure functions, business logic
      ║     test suite)      ║
      ╚══════════════════════╝
```

---

## 3. Python Backend Testing (pytest)

### 3.1 Configuration

```toml
# apps/api/pyproject.toml

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = [
    "--strict-markers",
    "--tb=short",
    "-x",                         # Stop after first failure
    "--cov=.",
    "--cov-report=term-missing",
    "--cov-fail-under=85",        # Fail CI if coverage drops below 85%
]
markers = [
    "unit: Fast unit tests with no external dependencies",
    "integration: Tests requiring database or Redis",
    "ai: Tests requiring LLM API calls (skipped in CI unless flag set)",
    "slow: Tests that take > 5 seconds",
]
```

### 3.2 Directory Structure

```
apps/api/tests/
├── conftest.py               # Shared fixtures
├── factories.py              # Test data factories
├── unit/
│   ├── test_grant_scoring.py
│   ├── test_compliance_checker.py
│   ├── test_eligibility_screener.py
│   ├── test_rag_retrieval.py
│   └── test_deadline_calculator.py
├── integration/
│   ├── test_auth_endpoints.py
│   ├── test_application_endpoints.py
│   ├── test_grant_search.py
│   ├── test_document_upload.py
│   ├── test_celery_tasks.py
│   └── test_websocket.py
└── ai/
    ├── test_generation_quality.py
    └── test_prompt_templates.py
```

### 3.3 Fixtures

```python
# tests/conftest.py

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from main import app
from database import Base
from tests.factories import OrgFactory, UserFactory, GrantFactory

TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5432/orchestragrant_test"

@pytest_asyncio.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(engine):
    async with AsyncSession(engine) as session:
        async with session.begin():
            yield session
            await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest_asyncio.fixture
async def org(db_session):
    return await OrgFactory.create(session=db_session)

@pytest_asyncio.fixture
async def admin_user(db_session, org):
    return await UserFactory.create(session=db_session, org=org, role="admin")

@pytest_asyncio.fixture
async def admin_client(client, admin_user):
    # Login and attach token to client
    resp = await client.post("/v1/auth/login", json={
        "email": admin_user.email,
        "password": "TestPassword123!"
    })
    token = resp.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client
```

### 3.4 Test Data Factories

```python
# tests/factories.py

from factory import Factory, LazyAttribute, SubFactory, Sequence
from factory.alchemy import SQLAlchemyModelFactory
import factory

from models import Organization, User, Grant, Funder, Application

class OrgFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Organization
        sqlalchemy_session_persistence = "commit"
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    name = factory.Sequence(lambda n: f"Test Orchestra {n}")
    ein = factory.Sequence(lambda n: f"99-{n:07d}")

class UserFactory(SQLAlchemyModelFactory):
    class Meta:
        model = User
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    first_name = "Test"
    last_name = "User"
    role = "staff"
    org = SubFactory(OrgFactory)
    is_active = True

class GrantFactory(SQLAlchemyModelFactory):
    class Meta:
        model = Grant
    
    id = factory.LazyFunction(lambda: str(uuid4()))
    name = factory.Sequence(lambda n: f"Test Grant {n}")
    grant_type = "project"
    award_min = 10000
    award_max = 50000
    status = "verified"
    funder = SubFactory(FunderFactory)
```

### 3.5 Mocking LLM Calls

LLM calls are always mocked in unit and integration tests:

```python
# tests/unit/test_compliance_checker.py

import pytest
from unittest.mock import AsyncMock, patch
from ai.compliance import ComplianceChecker

@pytest.mark.unit
async def test_compliance_checker_missing_elements():
    mock_response = {
        "elements_present": ["target_audience", "timeline"],
        "elements_missing": ["project_budget", "evaluation_plan"],
        "score": 50,
    }
    
    with patch("ai.llm_client.LLMClient.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        
        checker = ComplianceChecker()
        result = await checker.check(
            section_text="We will serve 500 students in spring 2027.",
            required_elements=["target_audience", "timeline", "project_budget", "evaluation_plan"]
        )
    
    assert result.score == 50
    assert "project_budget" in [e.label for e in result.elements if not e.present]
    assert result.band == "needs_work"
```

### 3.6 Integration Test Example

```python
# tests/integration/test_application_endpoints.py

@pytest.mark.integration
async def test_create_application_and_advance_stage(admin_client, org, db_session):
    # Create grant and cycle
    grant = await GrantFactory.create(session=db_session)
    cycle = await GrantCycleFactory.create(session=db_session, grant=grant)
    
    # Create application
    resp = await admin_client.post("/v1/applications", json={
        "grant_id": str(grant.id),
        "grant_cycle_id": str(cycle.id),
        "amount_requested": 25000,
        "application_deadline": "2027-03-01T00:00:00Z",
        "sections": [
            {"section_name": "Org Overview", "section_order": 0},
            {"section_name": "Project Description", "section_order": 1},
        ]
    })
    assert resp.status_code == 201
    app_id = resp.json()["id"]
    assert resp.json()["stage"] == "in_progress"
    
    # Advance to staff_review
    resp = await admin_client.post(f"/v1/applications/{app_id}/stage", json={
        "target_stage": "staff_review",
        "comment": "Sections drafted."
    })
    assert resp.status_code == 200
    assert resp.json()["stage"] == "staff_review"
    
    # Verify stage history recorded
    resp = await admin_client.get(f"/v1/applications/{app_id}/stage-history")
    assert len(resp.json()["data"]) == 1
    assert resp.json()["data"][0]["to_stage"] == "staff_review"

@pytest.mark.integration
async def test_invalid_stage_transition_blocked(admin_client, org, db_session):
    # Cannot jump from in_progress directly to submitted
    application = await ApplicationFactory.create(session=db_session, stage="in_progress")
    
    resp = await admin_client.post(f"/v1/applications/{application.id}/stage", json={
        "target_stage": "submitted"
    })
    assert resp.status_code == 422
    assert "Invalid stage transition" in resp.json()["detail"]
```

---

## 4. Frontend Testing (Vitest + React Testing Library)

### 4.1 Configuration

```typescript
// apps/web/vitest.config.ts

import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    globals: true,
    coverage: {
      reporter: ['text', 'lcov'],
      exclude: ['node_modules/', '.next/'],
      thresholds: { lines: 80, functions: 80 },
    },
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },
});
```

### 4.2 Component Test Example

```typescript
// apps/web/tests/unit/components/DeadlineCard.test.tsx

import { render, screen } from '@testing-library/react';
import { DeadlineCard } from '@/components/deadlines/DeadlineCard';

const mockDeadline = {
  id: 'deadline-1',
  title: 'NEA Art Works Application',
  dueDate: '2027-01-15T00:00:00Z',
  urgency: 'warning' as const,
  daysUntil: 22,
  deadlineType: 'application' as const,
  applicationId: 'app-1',
  isComplete: false,
};

describe('DeadlineCard', () => {
  it('renders deadline title and days remaining', () => {
    render(<DeadlineCard deadline={mockDeadline} />);
    
    expect(screen.getByText('NEA Art Works Application')).toBeInTheDocument();
    expect(screen.getByText('22 days')).toBeInTheDocument();
  });
  
  it('applies warning styling when urgency is warning', () => {
    render(<DeadlineCard deadline={mockDeadline} />);
    
    const card = screen.getByRole('article');
    expect(card).toHaveClass('border-amber-400');
  });
  
  it('marks as complete when isComplete is true', () => {
    render(<DeadlineCard deadline={{ ...mockDeadline, isComplete: true }} />);
    
    expect(screen.getByRole('checkbox')).toBeChecked();
  });
});
```

### 4.3 Custom Hook Test Example

```typescript
// apps/web/tests/unit/hooks/useApplicationStage.test.ts

import { renderHook, act } from '@testing-library/react';
import { useApplicationStage } from '@/hooks/useApplicationStage';
import { createQueryClientWrapper } from '../utils';

vi.mock('@/lib/api', () => ({
  transitionStage: vi.fn().mockResolvedValue({
    id: 'app-1',
    stage: 'staff_review',
  }),
}));

describe('useApplicationStage', () => {
  it('transitions stage and invalidates application queries', async () => {
    const wrapper = createQueryClientWrapper();
    const { result } = renderHook(
      () => useApplicationStage('app-1'),
      { wrapper }
    );
    
    await act(async () => {
      await result.current.transitionTo('staff_review', 'Ready for review');
    });
    
    expect(result.current.isSuccess).toBe(true);
  });
});
```

---

## 5. End-to-End Testing (Playwright)

### 5.1 Configuration

```typescript
// playwright.config.ts

import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,             // Sequential to avoid race conditions
  workers: 2,
  timeout: 60_000,
  
  use: {
    baseURL: process.env.BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry',
  },
  
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  
  globalSetup: './tests/e2e/global-setup.ts',  // Login and store auth state
});
```

### 5.2 Critical User Path Tests

The following 10 user paths are covered by E2E tests and must pass before every production deployment:

| Test | Path |
|---|---|
| `auth.spec.ts` | Login → MFA → Dashboard |
| `org-setup.spec.ts` | New org → setup wizard → profile complete |
| `document-upload.spec.ts` | Upload PDF → processing complete → atom count displayed |
| `grant-search.spec.ts` | Search grants → filter → view detail → add to watchlist |
| `discovery-queue.spec.ts` | View discovery queue → approve grant → appears in database |
| `create-application.spec.ts` | Search grant → create application → sections list displays |
| `ai-generation.spec.ts` | Open section → generate → content appears → compliance shown |
| `stage-transition.spec.ts` | Advance application through all stages to submitted |
| `deadline-calendar.spec.ts` | View deadline calendar → deadlines displayed correctly |
| `analytics-dashboard.spec.ts` | View analytics → KPI cards display non-zero data |

### 5.3 E2E Test Example

```typescript
// tests/e2e/ai-generation.spec.ts

import { test, expect } from '@playwright/test';

test.describe('AI Section Generation', () => {
  test.use({ storageState: 'tests/e2e/auth-state.json' });
  
  test('generates section and shows compliance check', async ({ page }) => {
    // Navigate to an existing in-progress application
    await page.goto('/applications/e2e-test-app-id');
    await page.getByRole('tab', { name: 'Sections' }).click();
    
    // Select first section
    await page.getByText('Organization Overview').click();
    
    // Click Generate
    await page.getByRole('button', { name: 'Generate' }).click();
    
    // Configure generation options
    await page.getByLabel('Balanced').check();
    await page.getByLabel('Auto-detect from funder type').check();
    await page.getByRole('button', { name: 'Generate →' }).click();
    
    // Wait for generation to complete (up to 60 seconds)
    await expect(page.getByRole('status', { name: 'Generating' }))
      .toBeVisible({ timeout: 5000 });
    await expect(page.getByRole('status', { name: 'Generating' }))
      .toBeHidden({ timeout: 60000 });
    
    // Verify content appeared in editor
    const editor = page.getByRole('textbox', { name: 'Section content' });
    const content = await editor.textContent();
    expect(content?.length).toBeGreaterThan(100);
    
    // Verify compliance check is shown
    await expect(page.getByText('Compliance Check')).toBeVisible();
    await expect(page.getByTestId('compliance-score')).toBeVisible();
    
    // Verify source atoms are listed
    await expect(page.getByText('Sources used')).toBeVisible();
  });
});
```

---

## 6. AI Generation Quality Testing

AI output quality is tested independently of the E2E suite, since it involves real LLM calls and is run on a separate schedule (not every CI run).

### 6.1 LLM Judge Evaluation

```python
# tests/ai/test_generation_quality.py

import pytest
from ai.evaluator import LLMJudge

@pytest.mark.ai
async def test_generated_section_is_specific():
    """Section should contain org-specific details, not generic filler."""
    
    evaluator = LLMJudge()
    result = await generate_section_for_test_org(
        section_type="organization_overview",
        org_profile=FULL_TEST_ORG_PROFILE,
    )
    
    evaluation = await evaluator.evaluate(
        generated_text=result.content,
        rubric={
            "specificity": "Does the text mention specific programs, dates, or numbers?",
            "accuracy": "Are all factual claims consistent with the source documents?",
            "relevance": "Is the text appropriate for an orchestral grant application?",
            "coherence": "Is the text well-organized and professional?",
        }
    )
    
    assert evaluation.scores["specificity"] >= 4, \
        f"Low specificity score: {evaluation.scores['specificity']}\n{evaluation.feedback}"
    assert evaluation.scores["accuracy"] >= 4, \
        f"Accuracy concern: {evaluation.feedback}"
    assert evaluation.scores["coherence"] >= 4

@pytest.mark.ai
async def test_generated_text_contains_no_hallucinated_figures():
    """Dollar amounts in generated text must match source documents."""
    
    result = await generate_section_for_test_org(
        section_type="budget_narrative",
        org_profile=FULL_TEST_ORG_PROFILE,
    )
    
    # Extract all dollar amounts from generated text
    amounts = extract_dollar_amounts(result.content)
    
    # Compare against amounts in source documents
    allowed_amounts = extract_amounts_from_test_org_documents()
    
    for amount in amounts:
        assert any(abs(amount - allowed) < 500 for allowed in allowed_amounts), \
            f"${amount:,} not found in source documents — potential hallucination"
```

### 6.2 Evaluation Cadence

| Test Type | When Run |
|---|---|
| Automated LLM quality tests | Weekly (scheduled CI job) |
| User feedback rating analysis | Monthly review |
| A/B prompt comparison | When prompt changes are made |
| Human expert audit | Quarterly (platform team reviews 20 random outputs) |

---

## 7. Performance Testing (k6)

### 7.1 Load Test Scenarios

```javascript
// tests/performance/api-load.test.js

import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    // Steady-state: simulate normal business day
    normal_load: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10m',
    },
    // Peak: simulate Monday morning (deadlines visible, everyone logging in)
    peak_load: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 200 },
        { duration: '5m', target: 200 },
        { duration: '2m', target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000'],    // 95% of requests < 2s
    http_req_failed: ['rate<0.01'],        // < 1% error rate
  },
};

const BASE_URL = 'https://staging.orchestragrant.com';

export default function () {
  // Login
  const loginResp = http.post(`${BASE_URL}/v1/auth/login`, JSON.stringify({
    email: __ENV.TEST_EMAIL,
    password: __ENV.TEST_PASSWORD,
  }), { headers: { 'Content-Type': 'application/json' } });
  
  check(loginResp, { 'login 200': (r) => r.status === 200 });
  const token = loginResp.json('access_token');
  
  const headers = {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
  
  // Browse grant database
  const grantsResp = http.get(`${BASE_URL}/v1/grants?limit=25`, { headers });
  check(grantsResp, { 'grants 200': (r) => r.status === 200 });
  
  // View dashboard
  const dashResp = http.get(`${BASE_URL}/v1/analytics/summary`, { headers });
  check(dashResp, { 'analytics 200': (r) => r.status === 200 });
  
  sleep(3);
}
```

### 7.2 Frontend Performance (Lighthouse CI)

```yaml
# .github/workflows/lighthouse.yml

- name: Run Lighthouse CI
  uses: treosh/lighthouse-ci-action@v11
  with:
    urls: |
      https://staging.orchestragrant.com
      https://staging.orchestragrant.com/grants
    budgetPath: ./lighthouse-budget.json

# lighthouse-budget.json
{
  "performance": [{"numericValue": 85, "metric": "score"}],
  "accessibility": [{"numericValue": 95, "metric": "score"}],
  "best-practices": [{"numericValue": 90, "metric": "score"}],
  "seo": [{"numericValue": 80, "metric": "score"}]
}
```

---

## 8. Security Testing

### 8.1 OWASP ZAP Scan (CI)

```yaml
# .github/workflows/security-scan.yml

- name: Run OWASP ZAP baseline scan
  uses: zaproxy/action-baseline@v0.12.0
  with:
    target: 'https://staging.orchestragrant.com'
    rules_file_name: '.zap/rules.tsv'
    cmd_options: '-a'              # Ajax spider
```

A ZAP rules file suppresses known false positives. Any new MEDIUM or HIGH alerts fail the CI build.

### 8.2 Dependency Auditing

- **Python:** `pip-audit` runs in CI; critical/high vulnerabilities fail the build
- **Node.js:** `npm audit` at level `high`; critical/high vulnerabilities fail the build
- **Container images:** ECR image scanning on push; CRITICAL CVEs block deployment

---

## 9. Test Data Management

### 9.1 Test Database

- Separate PostgreSQL database `orchestragrant_test`
- Recreated fresh at the start of each CI run
- Seed script loads: 5 test orgs, 20 grants, 50 applications (varied stages), 10 awards

### 9.2 E2E Test Data

- One dedicated test organization per environment (staging/dev)
- Auth state stored in `tests/e2e/auth-state.json` (generated by `global-setup.ts` using a test user)
- Test applications are pre-created with known IDs for deterministic E2E paths

### 9.3 Data Cleanup

- Unit tests: fully mocked, no database
- Integration tests: use transactions rolled back after each test (no cleanup needed)
- E2E tests: created data tagged with `e2e_created: true`; cleanup job runs after E2E suite

---

## 10. Coverage Requirements

| Service | Minimum Coverage |
|---|---|
| API (Python) | 85% line coverage |
| AI Service (Python) | 80% line coverage |
| Discovery Service (Python) | 80% line coverage |
| Frontend components | 80% line coverage |
| Frontend hooks/utils | 85% line coverage |

Coverage is enforced in CI. PRs that drop coverage below threshold require explicit approval from a senior engineer.

---

*Last Updated: 2026-05-01*
