# AWA Development Guidelines

## Commands
- Install: `uv venv && uv pip install -e .`
- Run: `uv run awa`
- Run specific workflow: `uv run awa run workflows/basic_chat.yaml`
- Lint: `ruff check src/`
- Type check: `mypy src/`

## Code Style
- Use PEP 8 conventions with 4-space indentation
- Type hints are required for all function parameters and return values
- Use Pydantic for data validation and model definitions
- Error handling: Use custom exception classes from `errors.py`
- Structure: Organize code in vertical slices (feature-based directories)
- Imports: Standard library first, then third-party, then local modules
- Documentation: Docstrings for all classes and functions using Google style

## Naming Conventions
- Classes: PascalCase
- Functions/methods: snake_case
- Variables: snake_case
- Constants: UPPER_SNAKE_CASE
- File names: snake_case.py

## Workflow Guidelines
- Use YAML for workflow definitions
- Follow schema defined in workflow_model.py
- Use Pydantic validators for model validation