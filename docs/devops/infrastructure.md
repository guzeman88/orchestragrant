# DevOps & Infrastructure

**Project:** OrchestraGrant Platform  
**Version:** 1.0  
**Last Updated:** 2026-05-01

---

## 1. Overview

OrchestraGrant runs on AWS using a fully containerized, infrastructure-as-code architecture. All infrastructure is provisioned via Terraform. All deployments happen via GitHub Actions CI/CD pipelines. This document defines the complete DevOps setup.

---

## 2. Repository Structure

```
orchestragrant/
├── apps/
│   ├── web/                    # Next.js 15 frontend
│   ├── api/                    # FastAPI main API
│   ├── ai-service/             # FastAPI AI generation service
│   └── discovery-service/      # FastAPI discovery + scraper
├── packages/
│   ├── types/                  # Shared TypeScript types + Zod schemas
│   └── email-templates/        # React Email templates
├── infrastructure/
│   ├── terraform/
│   │   ├── modules/
│   │   │   ├── ecs/
│   │   │   ├── rds/
│   │   │   ├── elasticache/
│   │   │   ├── s3/
│   │   │   ├── alb/
│   │   │   ├── cloudfront/
│   │   │   ├── waf/
│   │   │   ├── secrets/
│   │   │   └── monitoring/
│   │   ├── environments/
│   │   │   ├── dev/
│   │   │   ├── staging/
│   │   │   └── prod/
│   │   └── main.tf
│   └── docker/
│       ├── api.Dockerfile
│       ├── ai-service.Dockerfile
│       ├── discovery-service.Dockerfile
│       └── nginx/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy-staging.yml
│       └── deploy-prod.yml
├── docker-compose.yml          # Local development
├── docker-compose.test.yml     # Test environment
└── Makefile                    # Developer convenience commands
```

---

## 3. Environments

| Environment | Purpose | URL | Auto-deploy |
|---|---|---|---|
| Local | Developer workstation | http://localhost:3000 | N/A |
| Dev | Feature branch integration | dev.orchestragrant.com | On PR merge to `develop` |
| Staging | Pre-production validation | staging.orchestragrant.com | On merge to `main` |
| Production | Live customers | app.orchestragrant.com | Manual gate after staging |

### Environment Variables

Each environment has a `.env.{environment}` template in the repo (values excluded from git). Actual values are stored in AWS Secrets Manager and injected at ECS task launch.

```bash
# Template: .env.example
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
LLAMAPARSE_API_KEY=...
JWT_PRIVATE_KEY_ARN=arn:aws:secretsmanager:...
STRIPE_SECRET_KEY=...
STRIPE_WEBHOOK_SECRET=...
AWS_SES_FROM_ADDRESS=noreply@orchestragrant.com
GRANTS_GOV_API_KEY=...
CANDID_CLIENT_ID=...
CANDID_CLIENT_SECRET=...
SENTRY_DSN=...
NEXT_PUBLIC_SENTRY_DSN=...
NEXT_PUBLIC_API_BASE_URL=https://api.orchestragrant.com/v1
NEXT_PUBLIC_WS_URL=wss://api.orchestragrant.com/ws
```

---

## 4. Docker Configuration

### 4.1 API Dockerfile

```dockerfile
# infrastructure/docker/api.Dockerfile

FROM python:3.12-slim AS base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY apps/api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS production
COPY apps/api/ .

# Non-root user for security
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--proxy-headers", "--forwarded-allow-ips", "*"]
```

### 4.2 Local Docker Compose

```yaml
# docker-compose.yml

version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: orchestragrant
      POSTGRES_PASSWORD: localdev
      POSTGRES_DB: orchestragrant
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./apps/api/migrations/seed:/docker-entrypoint-initdb.d

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  api:
    build:
      context: .
      dockerfile: infrastructure/docker/api.Dockerfile
      target: base
    environment:
      DATABASE_URL: postgresql://orchestragrant:localdev@postgres:5432/orchestragrant
      REDIS_URL: redis://redis:6379/0
      ENV: development
    env_file: .env.local
    ports:
      - "8000:8000"
    volumes:
      - ./apps/api:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    depends_on:
      - postgres
      - redis

  ai-service:
    build:
      context: .
      dockerfile: infrastructure/docker/ai-service.Dockerfile
      target: base
    environment:
      DATABASE_URL: postgresql://orchestragrant:localdev@postgres:5432/orchestragrant
      REDIS_URL: redis://redis:6379/0
    env_file: .env.local
    ports:
      - "8001:8001"
    volumes:
      - ./apps/ai-service:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8001 --reload
    depends_on:
      - postgres
      - redis

  celery-worker:
    build:
      context: .
      dockerfile: infrastructure/docker/api.Dockerfile
      target: base
    command: celery -A celery_app worker --loglevel=info --queues=default,ai,discovery
    env_file: .env.local
    volumes:
      - ./apps/api:/app
    depends_on:
      - postgres
      - redis

  web:
    build:
      context: ./apps/web
    environment:
      NEXT_PUBLIC_API_BASE_URL: http://localhost:8000/v1
      NEXT_PUBLIC_WS_URL: ws://localhost:8000/ws
    ports:
      - "3000:3000"
    volumes:
      - ./apps/web:/app
      - /app/node_modules
      - /app/.next

volumes:
  postgres_data:
  redis_data:
```

---

## 5. Terraform Infrastructure

### 5.1 Module Structure

```hcl
# infrastructure/terraform/environments/prod/main.tf

module "ecs" {
  source = "../../modules/ecs"
  
  environment     = "prod"
  api_image       = "${aws_ecr_repository.api.repository_url}:${var.api_image_tag}"
  ai_image        = "${aws_ecr_repository.ai_service.repository_url}:${var.ai_image_tag}"
  disco_image     = "${aws_ecr_repository.discovery.repository_url}:${var.discovery_image_tag}"
  
  api_cpu         = 1024
  api_memory      = 2048
  api_min_count   = 2
  api_max_count   = 10
  
  ai_cpu          = 2048
  ai_memory       = 4096
  ai_min_count    = 0         # Scale to zero when idle
  ai_max_count    = 8
  
  vpc_id          = module.vpc.vpc_id
  private_subnets = module.vpc.private_subnet_ids
  alb_target_group_arn = module.alb.api_target_group_arn
}

module "rds" {
  source = "../../modules/rds"
  
  environment          = "prod"
  instance_class       = "db.r7g.xlarge"
  allocated_storage    = 200
  multi_az             = true
  deletion_protection  = true
  backup_retention     = 14         # days
  
  vpc_id              = module.vpc.vpc_id
  private_subnets     = module.vpc.private_subnet_ids
  db_security_group   = module.ecs.ecs_security_group_id
}

module "elasticache" {
  source = "../../modules/elasticache"
  
  environment      = "prod"
  node_type        = "cache.r7g.large"
  num_cache_nodes  = 2              # Primary + replica
  at_rest_encryption = true
  transit_encryption = true
  
  vpc_id           = module.vpc.vpc_id
  private_subnets  = module.vpc.private_subnet_ids
}
```

### 5.2 ECS Task Definitions

```json
// infrastructure/terraform/modules/ecs/task-definitions/api.json.tpl

{
  "family": "orchestragrant-api-${environment}",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "${cpu}",
  "memory": "${memory}",
  "executionRoleArn": "${execution_role_arn}",
  "taskRoleArn": "${task_role_arn}",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "${image}",
      "portMappings": [
        {"containerPort": 8000, "protocol": "tcp"}
      ],
      "environment": [
        {"name": "ENV", "value": "${environment}"},
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:${region}:${account_id}:secret:orchestragrant/${environment}/database-url"
        },
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:secretsmanager:${region}:${account_id}:secret:orchestragrant/${environment}/redis-url"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/orchestragrant-api-${environment}",
          "awslogs-region": "${region}",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
```

### 5.3 Auto-Scaling

```hcl
# ECS API service auto-scaling
resource "aws_appautoscaling_target" "api" {
  max_capacity       = 10
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.api.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

resource "aws_appautoscaling_policy" "api_cpu" {
  name               = "api-cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api.resource_id
  scalable_dimension = aws_appautoscaling_target.api.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api.service_namespace

  target_tracking_scaling_policy_configuration {
    target_value = 70.0
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# AI service scales to zero using EventBridge scheduler
resource "aws_appautoscaling_scheduled_action" "ai_scale_in" {
  name               = "scale-in-overnight"
  service_namespace  = "ecs"
  resource_id        = "service/${aws_ecs_cluster.main.name}/${aws_ecs_service.ai.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  schedule           = "cron(0 2 * * ? *)"   # 2 AM UTC daily
  
  scalable_target_action {
    min_capacity = 0
    max_capacity = 0
  }
}
```

---

## 6. CI/CD Pipeline

### 6.1 CI Pipeline (`.github/workflows/ci.yml`)

Triggered on every push and PR.

```yaml
name: CI

on:
  push:
    branches: ['*']
  pull_request:
    branches: [main, develop]

jobs:
  lint-and-typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run typecheck
      - run: npm run lint

  test-api:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: orchestragrant_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r apps/api/requirements-dev.txt
      - run: pytest apps/api/tests/ --cov=apps/api --cov-report=xml -x
        env:
          DATABASE_URL: postgresql://test:test@localhost:5432/orchestragrant_test
          REDIS_URL: redis://localhost:6379/0
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY_TEST }}
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: npm ci
      - run: npm run test:unit --workspace=apps/web

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Bandit (Python SAST)
        run: pip install bandit && bandit -r apps/api apps/ai-service apps/discovery-service -ll
      - name: Run npm audit
        run: npm audit --audit-level=high

  build-images:
    needs: [lint-and-typecheck, test-api, test-frontend, security-scan]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.ref == 'refs/heads/develop'
    steps:
      - uses: actions/checkout@v4
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      - name: Build and push API image
        run: |
          docker build -t $ECR_REGISTRY/orchestragrant-api:$GITHUB_SHA \
            -f infrastructure/docker/api.Dockerfile .
          docker push $ECR_REGISTRY/orchestragrant-api:$GITHUB_SHA
```

### 6.2 Deploy to Staging

```yaml
# .github/workflows/deploy-staging.yml
# Triggered after successful build on main branch

- name: Deploy to Staging
  run: |
    aws ecs update-service \
      --cluster orchestragrant-staging \
      --service orchestragrant-api \
      --force-new-deployment \
      --region us-east-1

- name: Wait for stable deployment
  run: |
    aws ecs wait services-stable \
      --cluster orchestragrant-staging \
      --services orchestragrant-api \
      --region us-east-1

- name: Run integration tests against staging
  run: npx playwright test --project=staging
  env:
    BASE_URL: https://staging.orchestragrant.com
    TEST_USER_EMAIL: ${{ secrets.STAGING_TEST_EMAIL }}
    TEST_USER_PASSWORD: ${{ secrets.STAGING_TEST_PASSWORD }}
```

### 6.3 Deploy to Production

```yaml
# .github/workflows/deploy-prod.yml
# Triggered manually after staging validation

on:
  workflow_dispatch:
    inputs:
      image_tag:
        description: 'Image tag to deploy (default: latest from main)'
        required: false

# Requires approval from the "production-deploy" GitHub environment (1 required reviewer)
environment: production-deploy

- name: Deploy to Production
  run: |
    aws ecs update-service \
      --cluster orchestragrant-prod \
      --service orchestragrant-api \
      --force-new-deployment
      
- name: Wait for stable
  run: aws ecs wait services-stable ...

- name: Notify deployment complete
  uses: slackapi/slack-github-action@v1
  with:
    payload: '{"text":"✅ Production deployment complete: ${{ github.sha }}"}'
```

---

## 7. Database Migrations

Migrations are managed using **Alembic** (Python/SQLAlchemy).

```bash
# Create a new migration
cd apps/api
alembic revision --autogenerate -m "add_audit_log_table"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

Migrations run automatically in CI before test execution. In production, migrations run as a separate one-off ECS task before the new service version receives traffic (zero-downtime migration pattern).

---

## 8. Monitoring & Observability

### 8.1 CloudWatch Dashboards

One dashboard per service with:
- Request rate and error rate (from ALB access logs)
- ECS CPU and memory utilization
- Response time p50/p95/p99 (from OTEL traces)
- Active tasks (Celery queue depth)
- RDS connections, read/write IOPS, replica lag
- ElastiCache hit rate, memory usage

### 8.2 Alerting (PagerDuty integration)

| Alert | Threshold | Severity |
|---|---|---|
| API error rate | > 5% over 5 minutes | P2 |
| API error rate | > 20% over 2 minutes | P1 |
| API p99 response time | > 5 seconds | P2 |
| RDS CPU | > 80% over 10 minutes | P2 |
| RDS free storage | < 20 GB | P2 |
| RDS replica lag | > 30 seconds | P1 |
| ElastiCache evictions | > 100/minute | P3 |
| Celery queue depth | > 500 jobs | P2 |
| ECS service unhealthy tasks | > 0 for 5 minutes | P1 |
| SSL certificate expiry | < 30 days | P2 |

### 8.3 Distributed Tracing

OpenTelemetry SDK instrumented in all Python services. Traces exported to AWS X-Ray. Every incoming HTTP request generates a root span; downstream calls (database, Redis, OpenAI) are child spans.

Trace context is propagated through:
- HTTP headers (`traceparent`, `tracestate`)
- Celery task kwargs (`_otel_context`)

---

## 9. Backup & Disaster Recovery

### 9.1 RDS Backups

- Automated daily snapshots (AWS RDS, 14-day retention)
- Cross-region snapshot copy to `us-west-2` daily
- Point-in-time recovery enabled (5-minute granularity)
- RTO target: 1 hour; RPO target: 5 minutes

### 9.2 S3 Backups

- S3 versioning enabled on all buckets
- S3 replication rules copy all objects to backup bucket in `us-west-2`
- Lifecycle policy: versions older than 365 days transitioned to Glacier

### 9.3 Disaster Recovery Runbook

1. Declare incident in PagerDuty; notify on-call engineer
2. Assess impact: is the primary region completely unavailable?
3. If partial: identify affected service; restart or scale ECS service
4. If full region failure:
   a. Restore latest RDS snapshot in `us-west-2`
   b. Update Secrets Manager in DR region with connection strings
   c. Deploy ECS services in DR region using latest ECR images
   d. Update Route 53 DNS to point to DR ALB
   e. Verify health checks pass
   f. Communicate status to customers via status page

### 9.4 RTO/RPO Targets

| Scenario | RTO | RPO |
|---|---|---|
| Single service crash | 5 min (auto-restart) | 0 (stateless) |
| Database failover (Multi-AZ) | 60 sec | 0 |
| Full region failure | 1 hour | 5 minutes |

---

## 10. Developer Convenience Commands

```makefile
# Makefile

# Start local development environment
dev:
	docker-compose up -d postgres redis
	cd apps/web && npm run dev &
	cd apps/api && uvicorn main:app --reload --port 8000 &
	cd apps/ai-service && uvicorn main:app --reload --port 8001

# Run all tests
test:
	docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# Run database migrations
migrate:
	cd apps/api && alembic upgrade head

# Generate a new migration
migration name="":
	cd apps/api && alembic revision --autogenerate -m "$(name)"

# Seed local database
seed:
	cd apps/api && python scripts/seed_database.py

# Format code
fmt:
	cd apps/api && black . && isort .
	cd apps/web && npm run format

# Build all Docker images locally
build:
	docker build -t orchestragrant-api:local -f infrastructure/docker/api.Dockerfile .
	docker build -t orchestragrant-ai:local -f infrastructure/docker/ai-service.Dockerfile .
```

---

*Last Updated: 2026-05-01*
