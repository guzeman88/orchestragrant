# Security Specification

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Overview

OrchestraGrant stores sensitive organizational financial data, legal documents, board member personal information, and grant strategy intelligence. Security is not optional — a breach could compromise not only data but an organization's standing with funders. This document defines the security architecture for all layers of the system.

---

## 2. Authentication

### 2.1 Primary Authentication

- **Method:** Email + password with optional TOTP MFA
- **Password requirements:** Minimum 12 characters, must include uppercase, lowercase, number, and symbol; checked against HaveIBeenPwned API on registration and change
- **Password storage:** bcrypt with cost factor 12 (never plaintext or reversible hash)
- **JWT:** RS256 asymmetric signing; private key stored in AWS Secrets Manager; public key rotated every 90 days
- **Token lifetime:** 8 hours; silent refresh with refresh token (30-day lifetime, single-use)
- **Session invalidation:** Token blacklisting via Redis on explicit logout; all tokens invalidated on password change

### 2.2 MFA

- **Algorithm:** TOTP (RFC 6238, SHA-1, 30-second window, 6-digit codes)
- **Library:** PyOTP (server-side)
- **Setup:** QR code displayed once; recovery codes (8 × 16-char alphanumeric) generated and hashed before storage
- **Enforcement:** Admin can require MFA for all org users; enforced at next login after enablement
- **TOTP secret storage:** Encrypted reference to AWS Secrets Manager; never stored in PostgreSQL directly

### 2.3 SSO (Phase 2)

- **Protocol:** OAuth 2.0 / OIDC
- **Providers:** Google Workspace, Microsoft 365 (Entra ID)
- **Account linking:** SSO users linked by email address match; first login creates account if email not found
- **Role assignment:** Default role `staff`; admin must manually elevate role after SSO-linked account created

### 2.4 Invitation Links

- **Token:** 128-bit cryptographically random token; stored as SHA-256 hash only
- **Expiry:** 72 hours
- **Single use:** Token deleted on acceptance
- **Re-invite:** Admin can re-send invitation, generating a new token (previous token immediately invalidated)

---

## 3. Authorization (RBAC)

### 3.1 Role Definitions

| Role | Description |
|---|---|
| `admin` | Full access; user management; org configuration; billing |
| `staff` | Full application and document access; cannot manage users or billing |
| `artistic_director` | Read access to all; can comment and approve applications; cannot edit org profile |
| `board_member` | Read access to applications in board_review stage; approve/decline only; no document vault access |
| `read_only` | Read-only view of dashboard, pipeline, and analytics; no editing |

### 3.2 Permission Matrix

| Resource | admin | staff | artistic_director | board_member | read_only |
|---|---|---|---|---|---|
| Org profile — view | ✓ | ✓ | ✓ | ✓ | ✓ |
| Org profile — edit | ✓ | ✓ | ✗ | ✗ | ✗ |
| Documents — upload/view | ✓ | ✓ | ✓ | ✗ | ✗ |
| Grant database — browse | ✓ | ✓ | ✓ | ✗ | ✓ |
| Applications — create | ✓ | ✓ | ✗ | ✗ | ✗ |
| Applications — edit/draft | ✓ | ✓ | ✗ | ✗ | ✗ |
| Applications — comment | ✓ | ✓ | ✓ | ✓ | ✗ |
| Applications — approve | ✓ | ✓ | ✓ | ✓ | ✗ |
| Applications — submit | ✓ | ✓ | ✗ | ✗ | ✗ |
| Discovery queue — review | ✓ | ✓ | ✗ | ✗ | ✗ |
| Analytics — view | ✓ | ✓ | ✓ | ✓ | ✓ |
| Awards — manage | ✓ | ✓ | ✗ | ✗ | ✗ |
| Users — manage | ✓ | ✗ | ✗ | ✗ | ✗ |
| Billing — view/manage | ✓ | ✗ | ✗ | ✗ | ✗ |

### 3.3 RBAC Enforcement

- Permissions are enforced at the API layer (FastAPI dependency injection), not only the frontend
- Every protected API endpoint uses a dependency that checks `current_user.role` against the required permission
- Frontend hides UI elements for unauthorized actions (defense in depth — not a substitute for API enforcement)
- Row-Level Security (RLS) in PostgreSQL ensures org data isolation at the database level (see Database Schema)

---

## 4. Data Protection

### 4.1 Encryption at Rest

| Data | Storage | Encryption |
|---|---|---|
| Database records | AWS RDS PostgreSQL | AES-256 via AWS RDS encryption (KMS-managed key) |
| Documents and files | AWS S3 | AES-256 via S3 SSE-KMS |
| Redis cache | AWS ElastiCache | AES-256 (in-transit + at-rest encryption enabled) |
| Celery job payloads | Redis | Same as Redis |
| Logs | CloudWatch Logs | AES-256 via CloudWatch encryption |

### 4.2 Encryption in Transit

- All external-facing endpoints: TLS 1.3 minimum (TLS 1.2 not accepted)
- All inter-service communication within VPC: TLS (using private ACM certificates)
- Database connections: SSL/TLS required by RDS parameter group (`rds.force_ssl = 1`)
- Redis connections: TLS enabled on ElastiCache

### 4.3 Sensitive Field Handling

**Fields that must never be stored in plaintext in PostgreSQL:**

| Field | Storage Method |
|---|---|
| MFA TOTP secrets | Reference to AWS Secrets Manager entry |
| Funder portal passwords | Reference to AWS Secrets Manager entry |
| LLM API keys | AWS Secrets Manager |
| Stripe API keys | AWS Secrets Manager |
| SMTP credentials | AWS Secrets Manager |
| OAuth client secrets | AWS Secrets Manager |

No secrets are stored in environment variables, code, or configuration files in version control.

### 4.4 S3 Document Access

- S3 buckets: **no public access** (Block Public Access enabled at account and bucket level)
- Documents accessed by authenticated users only via **presigned URLs** (15-minute expiry for downloads)
- Grant PDF archives accessed by discovery service via IAM role, not user-facing URLs
- S3 bucket policy: only allows access from the platform's IAM roles; denies all other principals

### 4.5 Data Minimization

- Funder contact information (email, phone) collected only from publicly available sources
- No financial data stored beyond what is necessary for grant application (no credit card numbers, no bank account numbers)
- IP addresses logged in audit_log for security events; purged after 90 days
- User passwords are never logged (request bodies containing passwords are filtered in middleware)

---

## 5. API Security

### 5.1 Input Validation

- All API inputs validated via Pydantic v2 models before any business logic executes
- SQL injection: prevented by SQLAlchemy parameterized queries; no raw SQL with user input
- File uploads: MIME type validated server-side (not just client-declared); virus scanning via ClamAV on all uploads before indexing
- JSON depth limiting: max 10 levels of nesting; max 50 array items in nested structures

### 5.2 Rate Limiting

Implemented at the API Gateway (AWS WAF) and application layer (Redis token bucket):

| Endpoint Group | Rate Limit |
|---|---|
| Authentication (`/auth/login`) | 10 requests/minute per IP |
| Authentication (`/auth/login`) | 5 failed attempts → 15-minute lockout per user |
| General API | 300 requests/minute per authenticated user |
| AI generation endpoints | 20 requests/hour per org |
| File upload URL requests | 50 requests/hour per org |
| Discovery queue review | 200 requests/hour per org |

### 5.3 CORS

- Allowed origin: `https://app.orchestragrant.com` (exact match)
- No wildcard origins
- Credentials: allowed only for the exact origin
- Preflight cache: 600 seconds

### 5.4 Security Headers

All responses include:

```
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{random}'; ...
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=()
```

### 5.5 CSRF

- JWT-based API with `Authorization: Bearer` header is not vulnerable to CSRF (no cookie-based auth for API calls)
- Next.js server actions use CSRF token validation (built-in Next.js 15 behavior)

---

## 6. Infrastructure Security

### 6.1 Network Architecture

```
Internet
    │
    ▼
AWS WAF (OWASP rule group + rate limiting)
    │
    ▼
Application Load Balancer (public subnet)
    │
    ▼
ECS Services (private subnet — no direct internet access)
    │
    ├─ Main API
    ├─ AI Service
    └─ Discovery Service
    │
    ▼
RDS, ElastiCache, S3 (private subnet / VPC endpoints)
```

- All ECS tasks run in private subnets with no public IPs
- Outbound internet for ECS tasks via NAT Gateway (scraper, LLM API calls)
- RDS: no public accessibility; VPC-only access
- ElastiCache: VPC-only access
- S3: accessed via VPC endpoint (traffic does not leave AWS network)

### 6.2 IAM Principles

- Least privilege: each ECS task has an IAM role with only the permissions it needs
- No wildcard `*` resource permissions on any IAM policy
- IAM roles reviewed quarterly by security audit
- No IAM access keys for services (roles only); access keys restricted to CI/CD with 90-day rotation

### 6.3 Secrets Rotation

| Secret | Rotation Schedule |
|---|---|
| RDS master password | Every 30 days (automated via Secrets Manager) |
| LLM API keys | Every 90 days (manual; triggered by provider recommendation) |
| JWT signing key pair | Every 90 days (automated; old key validated for 24-hour overlap) |
| Stripe API keys | Every 180 days |

### 6.4 Vulnerability Management

- **Dependency scanning:** Dependabot on GitHub repository for all packages; critical vulnerabilities require patch within 7 days
- **Container image scanning:** Amazon ECR image scanning on every push; images with CRITICAL CVEs blocked from deployment
- **SAST:** Bandit (Python), ESLint security plugin (TypeScript) in CI pipeline; PRs blocked if high-severity findings
- **Penetration testing:** Annual third-party pentest; findings remediated within 30 days for Critical, 90 days for High

---

## 7. Audit Logging

All security-relevant events are written to the `audit_log` table and simultaneously streamed to CloudWatch Logs for immutable archival:

| Event Category | Events Logged |
|---|---|
| Authentication | Login success, login failure, logout, MFA enable/disable, password change, token refresh |
| Authorization | Permission denied events |
| User management | Invite sent, user created, role changed, user deactivated |
| Data access | Document download, application export |
| Data modification | Grant record edit, org profile edit, application stage change, submission |
| Admin actions | Org settings change, billing change |
| AI generation | All generation requests with input hash (no content) |

**Audit log integrity:** CloudWatch Logs export to S3 with Object Lock (WORM) for 2-year retention.

---

## 8. Privacy & Data Compliance

### 8.1 CCPA Compliance

- Privacy policy clearly discloses all data collected, uses, and sharing
- "Do Not Sell" is trivially satisfied (we do not sell data)
- Data deletion: Admin can request org data deletion; executed within 30 days; documented process
- Data portability: Admin can export all org data as JSON + ZIP of documents

### 8.2 Data Retention

| Data Category | Retention Period |
|---|---|
| Active org data | Retained while org subscription is active |
| Deleted documents | 30 days after soft delete, then purged |
| Audit logs | 2 years |
| IP address logs | 90 days |
| AI generation job logs | 1 year |
| Stripe billing data | 7 years (legal/tax requirement) |
| Cancelled org data | 90 days after cancellation, then purged (configurable) |

### 8.3 Data Processing Agreement

- DPA template available for enterprise customers on request
- All sub-processors listed: AWS, OpenAI (or Anthropic), Candid, SendGrid, Stripe
- Sub-processor agreements in place confirming appropriate security standards

---

## 9. Incident Response

### 9.1 Severity Levels

| Level | Description | Response Time |
|---|---|---|
| P0 — Critical | Active breach, data exfiltration, complete service outage | 1 hour |
| P1 — High | Security vulnerability with exploit path, significant service degradation | 4 hours |
| P2 — Medium | Security misconfiguration, partial data exposure risk | 24 hours |
| P3 — Low | Security improvement, non-exploitable finding | 7 days |

### 9.2 Breach Notification

- If customer data is confirmed exposed: notify affected organizations within 72 hours
- Notification includes: what data was affected, how it happened, what was done to contain it, what customer should do
- Regulatory notification (if applicable): state AG, FTC as required by CCPA and other applicable law

---

*Last Updated: 2026-05-01*
