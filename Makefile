.PHONY: help start dev up down build test lint format migrate

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker commands
start: ## One-click start (creates .env, builds, and launches)
	@bash start.sh

up: ## Start all services with Docker Compose
	docker compose up -d

down: ## Stop all services
	docker compose down

build: ## Build all Docker images
	docker compose build

refresh: ## Stop, rebuild from scratch, and restart all services
	docker compose down
	docker compose build --no-cache
	docker compose up -d
	@echo ""
	@echo "  Frontend:  http://localhost:$${FRONTEND_PORT:-3000}"
	@echo "  Backend:   http://localhost:$${BACKEND_PORT:-8000}"
	@echo "  API Docs:  http://localhost:$${BACKEND_PORT:-8000}/docs"

logs: ## Show logs from all services
	docker compose logs -f

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
	cd frontend && npm install

frontend-dev: ## Run frontend in development mode
	cd frontend && npm run dev

frontend-test: ## Run frontend tests
	cd frontend && npm test

frontend-lint: ## Lint frontend code
	cd frontend && npm run lint

frontend-build: ## Build frontend for production
	cd frontend && npm run build

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
