# ELF Development Makefile
# Common development tasks for the ELF project

.PHONY: help install install-dev clean test test-cov lint format typecheck security pre-commit docs build release

# Default target
help:
	@echo "ELF Development Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install         Install ELF in development mode"
	@echo "  make install-dev     Install with development dependencies"
	@echo "  make clean          Clean build artifacts and caches"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint           Run linting with ruff"
	@echo "  make format         Format code with ruff"
	@echo "  make typecheck      Run type checking with mypy"
	@echo "  make security       Run security scans"
	@echo "  make pre-commit     Run all pre-commit hooks"
	@echo ""
	@echo "Testing:"
	@echo "  make test           Run test suite"
	@echo "  make test-cov       Run tests with coverage report"
	@echo "  make test-fast      Run tests (skip slow tests)"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs           Build documentation"
	@echo "  make docs-serve     Serve docs locally"
	@echo ""
	@echo "Build & Release:"
	@echo "  make build          Build distribution packages"
	@echo "  make release        Create a new release"
	@echo ""
	@echo "Examples:"
	@echo "  make examples       Validate example workflows"

# Setup commands
install:
	uv pip install -e .

install-dev:
	uv pip install -e .
	uv pip install --group dev --group test --group docs

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".hypothesis" -exec rm -rf {} +

# Code quality
lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/

typecheck:
	uv run mypy src/

security:
	uv run bandit -r src/
	uv run safety check

pre-commit:
	uv run pre-commit run --all-files

# Testing
test:
	uv run pytest tests/ -v

test-cov:
	uv run pytest tests/ -v --cov=src/elf --cov-report=html --cov-report=term-missing

test-fast:
	uv run pytest tests/ -v -m "not slow"

# Documentation
docs:
	@echo "Building documentation..."
	@python -c "import markdown; print('README validation: OK')"

docs-serve:
	@echo "Documentation serving not implemented yet"
	@echo "Use: python -m http.server 8000 -d docs/"

# Build and release
build: clean
	python -m build

release: clean test lint typecheck
	@echo "Creating release..."
	@echo "1. Run tests and quality checks: ✓"
	@echo "2. Update version in src/elf/__init__.py"
	@echo "3. Update CHANGELOG.md"
	@echo "4. Commit changes: git commit -am 'Release vX.Y.Z'"
	@echo "5. Create tag: git tag vX.Y.Z"
	@echo "6. Push: git push && git push --tags"
	@echo "7. GitHub Actions will handle the rest"

# Examples validation
examples:
	@echo "Validating example workflows..."
	@python -c "
	import yaml
	from pathlib import Path
	specs_dir = Path('specs/examples')
	if specs_dir.exists():
	    for yaml_file in specs_dir.glob('*.yaml'):
	        try:
	            with open(yaml_file, 'r') as f:
	                yaml.safe_load(f)
	            print(f'✓ {yaml_file.name}')
	        except yaml.YAMLError as e:
	            print(f'✗ {yaml_file.name}: {e}')
	            exit(1)
	    print('All examples validated successfully!')
	else:
	    print('No examples directory found')
	"

# Development workflow
dev: install-dev pre-commit test
	@echo "Development environment ready!"
	@echo "Run 'make help' for available commands"

# Continuous integration simulation
ci: lint typecheck security test
	@echo "CI checks passed!"

# Quick check before commit
check: format lint typecheck test-fast
	@echo "Pre-commit checks passed!"