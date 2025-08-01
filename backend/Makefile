.PHONY: help install test lint format clean docker-build docker-run docker-stop

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code"
	@echo "  clean        - Clean up generated files"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker containers"
	@echo "  cli-test     - Test CLI functionality"
	@echo "  api-test     - Test API functionality"

# Install dependencies
install:
	pip install -r requirements.txt
	pip install pytest pytest-cov pytest-asyncio pytest-mock flake8 black isort mypy

# Run tests
test:
	pytest tests/ -v --cov=app --cov-report=term-missing

# Run tests with coverage report
test-coverage:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/"

# Run linting
lint:
	flake8 app/ --count --select=E9,F63,F7,F82 --show-source --statistics
	flake8 app/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
	black --check app/
	isort --check-only app/
	mypy app/ --ignore-missing-imports

# Format code
format:
	black app/
	isort app/

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf research_assistant.db

# Build Docker image
docker-build:
	docker build -t research-brief .

# Run with Docker Compose
docker-run:
	docker-compose up --build

# Stop Docker containers
docker-stop:
	docker-compose down

# Test CLI functionality
cli-test:
	python -m app.cli test

# Test API functionality
api-test:
	@echo "Starting API server..."
	@echo "Testing health endpoint..."
	curl -f http://localhost:8000/health || echo "API not running"

# Test monitoring features
monitoring-test:
	python test_monitoring.py

# Show monitoring status
monitoring-status:
	python -m app.cli monitoring

# Development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production server
prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# Generate example brief
example:
	python -m app.cli generate --topic "artificial intelligence trends 2024" --verbose

# Show user history
history:
	python -m app.cli history --user-id "cli-user"

# Show user stats
stats:
	python -m app.cli stats --user-id "cli-user"

# Show configuration
config:
	python -m app.cli config

# Security check
security:
	bandit -r app/
	safety check

# Full development setup
setup: install format lint test
	@echo "Development environment setup complete!"

# Pre-commit checks
pre-commit: format lint test
	@echo "Pre-commit checks passed!"

# CI checks (same as GitHub Actions)
ci: lint security test
	@echo "CI checks completed!" 