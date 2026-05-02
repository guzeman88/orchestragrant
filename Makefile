.DEFAULT_GOAL := help

DOCKER_COMPOSE := docker compose
PYTHON := python3.12
PNPM := pnpm

##@ Setup

.PHONY: setup
setup: ## Bootstrap the full local dev environment
	@echo "Installing Node dependencies..."
	$(PNPM) install
	@echo "Creating Python virtual environments..."
	$(PYTHON) -m venv apps/api/.venv
	$(PYTHON) -m venv apps/ai-service/.venv
	$(PYTHON) -m venv apps/discovery-service/.venv
	@echo "Installing Python dependencies..."
	apps/api/.venv/bin/pip install -r apps/api/requirements.txt -r apps/api/requirements-dev.txt
	apps/ai-service/.venv/bin/pip install -r apps/ai-service/requirements.txt
	apps/discovery-service/.venv/bin/pip install -r apps/discovery-service/requirements.txt
	@echo "Copying env file..."
	cp -n .env.example .env || true
	@echo "Setup complete! Run 'make dev' to start the local stack."

##@ Development

.PHONY: dev
dev: ## Start all services via Docker Compose
	$(DOCKER_COMPOSE) up --build -d
	@echo "Services started:"
	@echo "  Web:       http://localhost:3000"
	@echo "  API:       http://localhost:8000/docs"
	@echo "  AI Svc:    http://localhost:8001/docs"
	@echo "  Discovery: http://localhost:8002/docs"
	@echo "  PgAdmin:   http://localhost:5050"

.PHONY: dev-logs
dev-logs: ## Tail logs from all services
	$(DOCKER_COMPOSE) logs -f

.PHONY: dev-down
dev-down: ## Stop all Docker Compose services
	$(DOCKER_COMPOSE) down

.PHONY: dev-reset
dev-reset: ## Stop services and remove volumes (DESTRUCTIVE)
	$(DOCKER_COMPOSE) down -v

##@ Database

.PHONY: db-migrate
db-migrate: ## Run Alembic migrations
	$(DOCKER_COMPOSE) exec api alembic upgrade head

.PHONY: db-revision
db-revision: ## Create a new Alembic revision (MSG="description")
	$(DOCKER_COMPOSE) exec api alembic revision --autogenerate -m "$(MSG)"

.PHONY: db-rollback
db-rollback: ## Roll back the last Alembic migration
	$(DOCKER_COMPOSE) exec api alembic downgrade -1

.PHONY: db-seed
db-seed: ## Seed the database with development data
	$(DOCKER_COMPOSE) exec api python -m scripts.seed_db

##@ Testing

.PHONY: test
test: test-api test-web ## Run all tests

.PHONY: test-api
test-api: ## Run Python tests
	$(DOCKER_COMPOSE) exec api pytest tests/ -v --cov=. --cov-report=term-missing

.PHONY: test-web
test-web: ## Run frontend unit tests
	$(PNPM) --filter=@orchestragrant/web test:unit

.PHONY: test-e2e
test-e2e: ## Run Playwright E2E tests
	$(PNPM) --filter=@orchestragrant/web test:e2e

##@ Code Quality

.PHONY: lint
lint: ## Lint all code
	$(PNPM) lint
	$(DOCKER_COMPOSE) exec api ruff check .

.PHONY: format
format: ## Format all code
	$(PNPM) format
	$(DOCKER_COMPOSE) exec api ruff format .

.PHONY: typecheck
typecheck: ## Run TypeScript type checking
	$(PNPM) typecheck

##@ Utilities

.PHONY: logs-api
logs-api: ## Tail API logs
	$(DOCKER_COMPOSE) logs -f api

.PHONY: shell-api
shell-api: ## Open a shell in the API container
	$(DOCKER_COMPOSE) exec api bash

.PHONY: shell-db
shell-db: ## Open a psql shell
	$(DOCKER_COMPOSE) exec postgres psql -U orchestragrant -d orchestragrant

.PHONY: help
help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } /^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
