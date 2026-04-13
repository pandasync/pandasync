# Contributing

See [CONTRIBUTING.md](https://github.com/pandasync/pandasync/blob/main/CONTRIBUTING.md) in the repository root for full guidelines.

## Development Setup

```bash
cd sdks/python
uv sync --dev
```

## Running Tests

```bash
uv run pytest -v
```

## Linting

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```
