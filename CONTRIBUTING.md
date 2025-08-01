# 🤝 Contributing to Elf0

Thank you for your interest in contributing to Elf0! We're excited to have you join our community of developers building the future of AI agent workflows. This project thrives because of contributors like you.

## 🌟 Ways to Contribute

We welcome all kinds of contributions, not just code:

- **🐛 Bug reports** - Help us identify and fix issues
- **💡 Feature requests** - Suggest new capabilities
- **📝 Documentation** - Improve guides, examples, and API docs
- **🧪 Testing** - Write tests, test new features, improve test coverage
- **💻 Code** - Fix bugs, implement features, improve performance
- **🎯 Workflow examples** - Share useful YAML workflows in `specs/`
- **🛠️ Tools** - Create MCP servers or Python functions
- **📢 Community** - Help others in discussions, write blog posts

## 🚀 Quick Start for Contributors

### 1. Set Up Your Development Environment

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/emson/elf0.git
cd elf0

# Set up the development environment
uv venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e .

# Install development dependencies
uv pip install -e . --group dev

# Verify installation
uv run elf0 --help
```

### 2. Get API Keys (for testing)

You'll need at least one API key to test workflows:

```bash
# Choose one or more:
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
# Or install Ollama for local testing: https://ollama.ai/
```

### 3. Run the Test Suite

Before making changes, ensure everything works:

```bash
# Run all tests
uv run pytest tests/ --timeout=300

# Run tests with coverage
uv run pytest tests/ --cov=src/elf0 --timeout=300

# Run only unit tests (faster)
uv run pytest tests/ -m "not requires_external"

# Run integration tests (requires API keys)
ELF_RUN_INTEGRATION_TESTS=1 uv run pytest tests/
```

### 4. Verify Code Quality

```bash
# Lint code
 uv run ruff check src/ tests/

# Type check
mypy src/

# Security scan
uv run bandit -r src/
```

## 📋 Development Workflow

### Making Changes

1. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/your-feature-name
   # or: git checkout -b fix/issue-description
   ```

2. **Make your changes** following our [coding guidelines](#-code-style-guidelines)

3. **Test your changes**:
   ```bash
   # Run relevant tests
   uv run pytest tests/ -k "test_your_feature"
   
   # Test with a real workflow
   uv run elf0 agent specs/basic/chat_simple_v1.yaml --prompt "Test your changes"
   ```

4. **Check code quality**:
   ```bash
   uv run ruff check src/ tests/
   mypy src/
   ```

5. **Commit your changes**:
   ```bash
   git add .
   git commit -m "Add feature: brief description of what you added"
   ```

### Submitting a Pull Request

1. **Push your branch**:
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create a Pull Request** on GitHub with:
   - Clear title describing the change
   - Description explaining what and why
   - Link to any related issues
   - Screenshots/examples if applicable

3. **Address feedback** from maintainers

4. **Celebrate** when your PR is merged! 🎉

## 🎯 Code Style Guidelines

We follow the guidelines established in `CLAUDE.md`. Key points:

### Python Code Style
- **PEP 8** conventions with 4-space indentation
- **Type hints** required for all function parameters and return values
- **Pydantic** for data validation and model definitions
- **Early returns** when possible
- **Absolute imports** only (no relative imports)

### Naming Conventions
- **Classes**: `PascalCase`
- **Functions/methods**: `snake_case`
- **Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Files**: `snake_case.py`

### Documentation
- **Docstrings** for all classes and functions using Google style
- **File location comment** at the top: `# src/my_module/my_file.py`
- **Type aliases** for clarity: `StepID = str`

### Git Conventions
- **Commit messages** in imperative mood: "Fix bug" not "Fixed bug"
- **Branch names**: `feature/add-logging`, `fix/memory-leak`
- **Check status** before committing: `git status && git diff`

## 🧪 Testing Guidelines

### Writing Tests
- Place tests in the `tests/` directory mirroring `src/` structure
- Use descriptive test names: `test_workflow_runs_successfully_with_valid_yaml`
- Test both happy paths and error conditions
- Mock external dependencies (API calls, file system)

### Test Types
- **Unit tests** (`-m unit`): Fast, isolated, no external dependencies
- **Integration tests** (`-m integration`): Test component interactions
- **External tests** (`-m requires_external`): Require real APIs/services

### Running Specific Tests
```bash
# Test a specific file
uv run pytest tests/core/test_compiler.py

# Test a specific function
uv run pytest tests/core/test_compiler.py::test_compile_workflow

# Test with markers
uv run pytest tests/ -m "unit and not slow"
```

## 🐛 Reporting Issues

### Bug Reports
Use our [issue template](https://github.com/emson/elf0/issues/new) and include:

- **Clear title** summarising the problem
- **Environment details**: OS, Python version, elf0 version
- **Steps to reproduce** the issue
- **Expected vs actual behaviour**
- **Error messages** (full stack traces help!)
- **YAML workflow** if relevant (anonymise sensitive data)

### Feature Requests
- **Describe the problem** you're trying to solve
- **Propose a solution** if you have ideas
- **Consider backwards compatibility**
- **Think about edge cases**

## 📁 Project Structure

Understanding the codebase:

```
src/elf0/
├── cli.py              # Command-line interface
├── core/               # Core functionality
│   ├── compiler.py     # YAML workflow compilation
│   ├── runner.py       # Workflow execution
│   ├── llm_client.py   # LLM integrations
│   └── nodes/          # Workflow node types
├── functions/          # Python function library
└── utils/              # Utility modules

specs/                  # Example workflows
├── basic/              # Simple examples
├── content/            # Content generation
├── examples/           # Feature demonstrations
└── utils/              # Workflow tools

tests/                  # Test suite
├── core/               # Core functionality tests
├── cli/                # CLI tests
└── integration/        # End-to-end tests
```

## 🎁 Types of Contributions We're Looking For

### High Priority
- **Bug fixes** - Especially with test cases
- **Documentation improvements** - Make it clearer for new users
- **Workflow examples** - Useful real-world YAML specs
- **Test coverage** - Help us reach 90%+ coverage

### Medium Priority
- **Performance improvements** - Faster workflow execution
- **New LLM integrations** - Support more models
- **MCP servers** - Useful tool integrations
- **CLI enhancements** - Better user experience

### Ideas Welcome
- **New node types** - Extend workflow capabilities
- **Workflow debugger** - Help users troubleshoot
- **Web interface** - Visual workflow builder
- **Workflow sharing** - Community marketplace

## 💬 Getting Help

- **GitHub Discussions**: Ask questions, share ideas
- **Issues**: Report bugs, request features
- **Discord** (coming soon): Real-time community chat

## 🏆 Recognition

Contributors are recognised in:
- **Release notes** for significant contributions
- **README acknowledgments** for major features
- **Git commit co-authorship** when pairing

## 📜 Code of Conduct

We're committed to providing a welcoming and inclusive experience for everyone. We expect all community members to:

### Our Standards
- **Be respectful** of differing viewpoints and experiences
- **Give and accept constructive feedback** gracefully
- **Focus on what's best** for the community and project
- **Show empathy** towards other community members

### Unacceptable Behaviour
- Harassment, discrimination, or inappropriate conduct
- Personal attacks or inflammatory comments
- Publishing private information without permission
- Any conduct that could be considered inappropriate in a professional setting

### Enforcement
Project maintainers will enforce these standards fairly and consistently. Reports can be made by contacting the project team at [ben@emson.dev](mailto:ben@emson.dev).

## 🔒 Security

If you find a security vulnerability, please email [ben@emson.dev](mailto:ben@emson.dev) instead of opening an issue. We'll work with you to resolve it promptly.

## 📄 License

By contributing to Elf0, you agree that your contributions will be licensed under the Apache License 2.0, the same licence as the project.

---

## 🚀 Ready to Contribute?

1. **Browse our [good first issues](https://github.com/emson/elf0/labels/good%20first%20issue)**
2. **Read the [project overview](docs/project_overview.md)** to understand our goals
3. **Join the conversation** in GitHub Discussions
4. **Say hello** - we're always happy to help new contributors get started!

Thank you for helping make Elf0 better for everyone! 🎉

---

*This contributing guide is inspired by open source best practices and tailored specifically for the Elf0 project. Have suggestions for improving it? Open an issue or PR!*
