# Elf Development Guidelines

## Commands
- Install: `uv venv && uv pip install -e .`
- Run: `uv run elf`
- Run specific workflow: `uv run elf agent workflows/basic_chat.yaml --prompt "Your prompt"`
- Test: `uv run pytest tests/ --timeout=300`
- Test with coverage: `uv run pytest tests/ --cov=src/elf --timeout=300`
- Lint: `ruff check src/`
- Type check: `mypy src/`
- Security scan: `uv pip install safety && uv run safety check` (optional - may conflict with pydantic versions)

## Git Commands
- Check status: `git status`
- View changes: `git diff`
- Add files: `git add <file>` or `git add .` for all changes
- Commit: `git commit -m "message"`
- Push: `git push origin <branch-name>`
- Pull latest: `git pull origin <branch-name>`
- Create branch: `git checkout -b <branch-name>`
- Switch branch: `git checkout <branch-name>`

## Git Guidelines
- Always check `git status` and `git diff` before committing
- Write clear, descriptive commit messages
- Use imperative mood in commit messages (e.g., "Fix bug" not "Fixed bug")
- Commit related changes together in logical units
- Never commit secrets, API keys, or sensitive information
- Use meaningful branch names (e.g., feature/add-logging, fix/memory-leak)
- Always review changes before pushing to remote
- For commits with Claude Code assistance, include attribution in commit message

## Code Style
- Use PEP 8 conventions with 4-space indentation
- Type hints are required for all function parameters and return values
- Use Pydantic for data validation and model definitions
- Error handling: Use custom exception classes from `errors.py`
- Structure: Organize code in vertical slices (feature-based directories)
- Imports: Standard library first, then third-party, then local modules
- Documentation: Docstrings for all classes and functions using Google style

## Coding Guidelines
- My project's programming language is python
- Use early returns when possible
- Always add documentation when creating new functions and classes
- Add a file location at the top of each file
- Always follow best practices for python and the libraries used
- Think hard about the best way to implement a feature
- Always focus on simple file structures and patterns, for flexibility and ease of maintenance
- Always try to understand the logic first and make minimal best practice code changes
- Always use absolute import paths and not relative import paths, DO NOT USE RELATIVE IMPORTS

## Documentation
- Always add a simple file location at the top of each file. e.g. `# src/my_module/my_file.py`, DO NOT USE `"""Location: src/my_module/my_file.py"""`

## Software Principles
- Where code could get complex use software design patterns to make it simple and maintainable
- Where code is ambiguous, always try to understand the logic first and make minimal best practice code changes
- Try to use compound functions made up of discreet and well defined subfunctions

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

## LLM-Friendly Code Principles
- Use descriptive, self-explanatory class and function names that clearly convey purpose
- Keep functions focused on a single responsibility with clear input/output relationships
- Create explicit interfaces using Protocol classes rather than implicit behavior
- Provide complete type hints for all parameters, return values, and class attributes
- Use explicit type aliases (e.g., `StepID = str`) to clarify the purpose of basic types
- Structure code to follow the natural lifecycle of operations (init → process → complete)
- Separate business logic from technical implementation details
- Avoid deeply nested code structures; prefer flat hierarchies with early returns
- Include meaningful comments explaining "why" not just "what" when logic is complex
- Use composition over inheritance to make relationships between components explicit
- Organize related functionality into cohesive classes rather than loose functions
- Design clear data flow paths that are easy to trace through the application
- Prefer explicit parameter passing over implicit shared state
- Keep class and function implementations concise (aim for <50 lines per function)
- Use Protocol classes or abstract base classes to define interfaces