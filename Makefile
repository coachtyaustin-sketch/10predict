.PHONY: dev backend frontend db cycle help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

db: ## Start database services (PostgreSQL + Neo4j)
	docker compose up -d postgres neo4j

backend: ## Run the backend API server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Run the frontend dev server
	cd frontend && npm run dev

dev: db ## Start everything for development
	@echo "Starting databases..."
	@sleep 3
	@echo "Starting backend and frontend..."
	$(MAKE) backend & $(MAKE) frontend

cycle: ## Manually trigger a research cycle
	cd backend && python -m scripts.run_manual_cycle manual

up: ## Start all services via Docker Compose
	docker compose up -d

down: ## Stop all services
	docker compose down

install: ## Install dependencies
	cd backend && pip install -e ".[dev]"
	cd frontend && npm install
