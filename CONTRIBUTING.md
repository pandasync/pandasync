# Contributing to PandaSync

Thank you for your interest in contributing to PandaSync! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch from `main`
4. Make your changes
5. Submit a pull request

## Development Setup

### Python SDK

```bash
cd sdks/python
uv sync --dev
```

### Running Tests

```bash
cd sdks/python
uv run pytest
```

### Linting and Formatting

```bash
cd sdks/python
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

## Code Style

- Python code follows `ruff` defaults with strict `mypy` type checking.
- Keep functions focused and small.
- Write tests for new functionality.
- Use type annotations on all public APIs.

## Commit Messages

- Use imperative mood ("Add feature" not "Added feature")
- Keep the first line under 72 characters
- Reference issues where applicable

## Pull Request Guidelines

- One logical change per PR
- Include tests for new functionality
- Ensure all CI checks pass
- Update documentation if behavior changes

## Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Include steps to reproduce for bugs
- Include your OS, Python version, and PandaSync version

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
