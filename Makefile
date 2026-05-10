# ============================================================
# OneAgent OS — Makefile
# ============================================================

.PHONY: help install dev test lint docker-up docker-down clean ci

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	pip install uv --quiet
	uv pip install -r requirements.txt --quiet
	uv pip install -r requirements-dev.txt --quiet
	pnpm install --quiet

dev-api: ## Start API in development mode
	uvicorn packages.api.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## Start Frontend in development mode
	pnpm --filter frontend dev

infra-up: ## Start infrastructure (Redis, Postgres, Qdrant, Ollama)
	docker compose up -d redis postgres qdrant ollama

infra-down: ## Stop infrastructure
	docker compose down

docker-up: ## Start all services with Docker Compose
	docker compose up -d --build

docker-down: ## Stop all Docker services
	docker compose down

test: ## Run all tests
	pytest -v --timeout=60

test-quick: ## Run quick unit tests (skip integration)
	pytest -v -m "not slow and not integration" --timeout=30

test-coverage: ## Run tests with coverage
	pytest -v --cov=packages --cov-report=html --cov-report=term --timeout=60

lint: ## Run linters
	ruff check packages/ --no-cache

typecheck: ## Run type checker
	mypy packages/core packages/api --ignore-missing-imports --no-incremental

format: ## Format code
	ruff format packages/

clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ coverage/ *.egg-info/

ci: lint typecheck test ## Run CI pipeline locally

precommit: format lint typecheck test-quick ## Run before every commit

benchmark: ## Run benchmarks
	python scripts/benchmark.py

validate: ## Run validation script
	bash scripts/validate.sh

.PHONY: help install dev-api dev-frontend infra-up infra-down docker-up docker-down
.PHONY: test test-quick test-coverage lint typecheck format clean ci precommit
.PHONY: benchmark validate
