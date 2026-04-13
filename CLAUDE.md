# CLAUDE.md -- PandaSync

## Project

PandaSync is an open-source networked audio transport protocol.
Tagline: "Plug-in simplicity. Broadcast grade. Completely open."

## Monorepo Layout

- `spec/` -- protocol specification
- `sdks/python/` -- Python SDK (pandasync)
- `controller/` -- web controller (future)
- `hardware/` -- hardware designs (future)
- `docs/` -- documentation site (MkDocs)
- `plan/` -- internal strategy docs (gitignored, never committed)

## Python SDK

- Location: `sdks/python/`
- Package: `pandasync` (imported as `import pandasync`)
- Managed with `uv`. Run `uv sync` from `sdks/python/` to install.
- Lint: `cd sdks/python && uv run ruff check src/ tests/`
- Format: `cd sdks/python && uv run ruff format src/ tests/`
- Type check: `cd sdks/python && uv run mypy src/`
- Test: `cd sdks/python && uv run pytest`
- CLI: `cd sdks/python && uv run pandasync --help`

## Conventions

- All public-facing text uses "PandaSync" (never "OpenAudioNet").
- Never reference competitors by name in code, comments, docs, or specs.
- License: Apache 2.0
- Python target: >= 3.11
- The `plan/` directory is gitignored and must never be committed.
- mDNS service type: `_pandasync._udp`
