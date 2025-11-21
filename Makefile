.PHONY: help install dev run test clean lint format

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Run development server with auto-reload"
	@echo "  make run        - Run production server"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linter (flake8)"
	@echo "  make format     - Format code with black"
	@echo "  make clean      - Remove cache files"
	@echo "  make shell      - Open pipenv shell"

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
