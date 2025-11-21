.PHONY: help install dev run test clean lint format

help:
	@echo "Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  make install         - Install dependencies"
	@echo "  make dev             - Run development server with auto-reload"
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

install:
	@echo "Installing dependencies..."
	pipenv install --dev

sync:
	@echo "Syncing dependencies..."
	pipenv sync --dev

dev:
	@echo "Starting development server..."
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
