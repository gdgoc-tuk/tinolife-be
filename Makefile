.PHONY: help install dev run test clean lint format docker-up docker-down docker-restart docker-logs

help:
	@echo "Available commands:"
	@echo ""
	@echo "Docker:"
	@echo "  make dev             - Start development environment with Docker Compose"
	@echo "  make docker-up       - Start Docker containers"
	@echo "  make docker-down     - Stop Docker containers"
	@echo "  make docker-restart  - Restart Docker containers"
	@echo "  make docker-logs     - View Docker logs"
	@echo "  make docker-clean    - Stop and remove all containers, volumes"
	@echo ""
	@echo "Development (Local):"
	@echo "  make install         - Install dependencies"
	@echo "  make dev-local       - Run development server locally (without Docker)"
	@echo "  make run             - Run production server"
	@echo "  make shell           - Open pipenv shell"
	@echo ""
	@echo "Database & Migrations:"
	@echo "  make migrate-create  - Create new migration (autogenerate)"
	@echo "  make migrate-up      - Apply all pending migrations"
	@echo "  make migrate-down    - Rollback last migration"
	@echo "  make migrate-history - Show migration history"
	@echo "  make migrate-current - Show current migration version"
	@echo "  make db-reset        - Reset database (WARNING: drops all data)"
	@echo ""
	@echo "Testing & Code Quality:"
	@echo "  make test            - Run tests"
	@echo "  make test-cov        - Run tests with coverage"
	@echo "  make lint            - Run linter (flake8)"
	@echo "  make format          - Format code with black"
	@echo "  make clean           - Remove cache files"

# Docker commands
dev:
	@echo "🚀 Starting development environment with Docker Compose..."
	@if [ ! -f .env ]; then \
		echo "Creating .env file from .env.example..."; \
		cp .env.example .env; \
	fi
	@docker-compose up --build -d
	@echo ""
	@echo "⏳ Waiting for containers to be ready..."
	@sleep 3
	@echo ""
	@echo "📋 Checking migration status..."
	@docker-compose logs app | grep -i "migration" || echo "   (Check logs with 'make docker-logs' for migration details)"
	@echo ""
	@echo "✅ Development environment is running!"
	@echo ""
	@echo "📝 Services:"
	@echo "   - API: http://localhost:8000"
	@echo "   - API Docs: http://localhost:8000/docs"
	@echo "   - Database: localhost:5432"
	@echo ""
	@echo "📊 Useful commands:"
	@echo "   - View logs: make docker-logs"
	@echo "   - View app logs: docker-compose logs -f app"
	@echo "   - Run migrations manually: docker-compose exec app pipenv run alembic upgrade head"
	@echo "   - Stop: make docker-down"
	@echo "   - Restart: make docker-restart"
	@echo ""

docker-up:
	@echo "Starting Docker containers..."
	docker-compose up -d

docker-down:
	@echo "Stopping Docker containers..."
	docker-compose down

docker-restart:
	@echo "Restarting Docker containers..."
	docker-compose restart

docker-logs:
	@echo "Viewing Docker logs..."
	docker-compose logs -f

docker-clean:
	@echo "Stopping and removing all containers, networks, and volumes..."
	docker-compose down -v --remove-orphans
	docker system prune -f

# Local development commands
install:
	@echo "Installing dependencies..."
	pipenv install --dev

sync:
	@echo "Syncing dependencies..."
	pipenv sync --dev

dev-local:
	@echo "Starting development server locally..."
	pipenv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run:
	@echo "Starting production server..."
	pipenv run uvicorn app.main:app --host 0.0.0.0 --port 8000

test:
	@echo "Running tests..."
	pipenv run pytest tests/ -v

test-cov:
	@echo "Running tests with coverage..."
	pipenv run pytest tests/ -v --cov=app --cov-report=html

lint:
	@echo "Running linter..."
	pipenv run flake8 app/ tests/
	pipenv run mypy app/

format:
	@echo "Formatting code..."
	pipenv run black app/ tests/

clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage

shell:
	@echo "Opening pipenv shell..."
	pipenv shell

update:
	@echo "Updating dependencies..."
	pipenv update

lock:
	@echo "Locking dependencies..."
	pipenv lock

# Database & Migration commands
db-init:
	@echo "Initializing database tables (dev only)..."
	pipenv run python -c "from app.core.database import init_db; init_db()"

db-reset:
	@echo "Resetting database (WARNING: drops all tables)..."
	pipenv run python -c "from app.core.database import drop_db, init_db; drop_db(); init_db()"

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter migration message: " msg; \
	pipenv run alembic revision --autogenerate -m "$$msg"

migrate-up:
	@echo "Running migrations..."
	pipenv run alembic upgrade head

migrate-down:
	@echo "Rolling back last migration..."
	pipenv run alembic downgrade -1

migrate-history:
	@echo "Showing migration history..."
	pipenv run alembic history

migrate-current:
	@echo "Showing current migration..."
	pipenv run alembic current

migrate-head:
	@echo "Creating new empty migration..."
	@read -p "Enter migration message: " msg; \
	pipenv run alembic revision -m "$$msg"
