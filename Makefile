# Makefile for Nautobot Chatbot Plugin
# Provides convenient commands for development and code quality

.PHONY: help install install-dev lint format check test clean security type-check pre-commit docs

# Default target
help:
	@echo "Available commands:"
	@echo "  install        Install package dependencies"
	@echo "  install-dev    Install package with development dependencies"
	@echo "  lint           Run all linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  check          Run all checks without fixing"
	@echo "  test           Run tests (when implemented)"
	@echo "  clean          Clean up build artifacts and caches"
	@echo "  security       Run security checks"
	@echo "  type-check     Run type checking with mypy"
	@echo "  pre-commit     Install and run pre-commit hooks"
	@echo "  docs           Generate documentation"
	@echo "  all-checks     Run all checks and formatters"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,ai]"
	pre-commit install

# Code formatting
format:
	@echo "Running code formatters..."
	black nautobot_chatbot/
	isort nautobot_chatbot/

# Linting
lint:
	@echo "Running linters..."
	flake8 nautobot_chatbot/
	pylint nautobot_chatbot/

# Type checking
type-check:
	@echo "Running type checks..."
	mypy nautobot_chatbot/

# Security checks
security:
	@echo "Running security checks..."
	bandit -r nautobot_chatbot/ -f json -o bandit-report.json || true
	safety check

# Check without fixing
check:
	@echo "Running all checks without modifications..."
	black --check --diff nautobot_chatbot/
	isort --check-only --diff nautobot_chatbot/
	flake8 nautobot_chatbot/
	pylint nautobot_chatbot/
	mypy nautobot_chatbot/

# Pre-commit hooks
pre-commit:
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Running pre-commit on all files..."
	pre-commit run --all-files

# Test (placeholder for when tests are implemented)
test:
	@echo "Running tests..."
	@echo "Tests not implemented yet - skipping for now"
	# pytest

# Clean up
clean:
	@echo "Cleaning up..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	find . -type f -name "bandit-report.json" -delete 2>/dev/null || true
	rm -rf build/ dist/ *.egg-info/

# Documentation (placeholder)
docs:
	@echo "Generating documentation..."
	@echo "Documentation generation not implemented yet"

# Run all checks and formatters
all-checks: format lint type-check security
	@echo "All checks completed!"

# Development workflow
dev-setup: install-dev pre-commit
	@echo "Development environment set up!"

# Quick development check
quick-check: format lint
	@echo "Quick development checks completed!"

# Release preparation
release-check: clean all-checks test
	@echo "Release checks completed!"

# Install specific linting tools
install-tools:
	pip install black isort flake8 pylint mypy bandit safety pre-commit

# Show tool versions
versions:
	@echo "Tool versions:"
	@python --version
	@black --version
	@isort --version
	@flake8 --version
	@pylint --version
	@mypy --version
	@bandit --version
	@safety --version
	@pre-commit --version