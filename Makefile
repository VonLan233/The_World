.PHONY: help dev up down build test lint format migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands
up: ## Start all services with Docker Compose
	docker-compose up -d

down: ## Stop all services
	docker-compose down

build: ## Build all Docker images
	docker-compose build

logs: ## Show logs from all services
	docker-compose logs -f

# Backend commands
backend-install: ## Install backend dependencies
	cd backend && uv sync

backend-dev: ## Run backend in development mode
	cd backend && uv run uvicorn src.the_world.main:app --reload --host 0.0.0.0 --port 8000

backend-test: ## Run backend tests
	cd backend && uv run pytest -v

backend-lint: ## Lint backend code
	cd backend && uv run ruff check src/ tests/

backend-format: ## Format backend code
	cd backend && uv run ruff format src/ tests/

backend-typecheck: ## Type check backend code
	cd backend && uv run mypy src/

# Frontend commands
frontend-install: ## Install frontend dependencies
	cd frontend && pnpm install

frontend-dev: ## Run frontend in development mode
	cd frontend && pnpm dev

frontend-test: ## Run frontend tests
	cd frontend && pnpm test

frontend-lint: ## Lint frontend code
	cd frontend && pnpm lint

frontend-build: ## Build frontend for production
	cd frontend && pnpm build

# Database commands
migrate: ## Run database migrations
	cd backend && uv run alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new MSG="description")
	cd backend && uv run alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	cd backend && uv run alembic downgrade -1

# Combined commands
dev: backend-install frontend-install ## Install all dependencies
	@echo "Dependencies installed. Run 'make up' to start services."

test: backend-test frontend-test ## Run all tests

lint: backend-lint frontend-lint ## Lint all code
