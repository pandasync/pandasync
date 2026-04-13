# PandaSync Python SDK

The official Python SDK for PandaSync -- networked audio transport.

## Installation

```bash
pip install pandasync
```

## Quick Start

### CLI

```bash
# Discover devices on your network
pandasync discover

# Route audio
pandasync connect "Mic Array:ch1-8" "Recorder:ch1-8"

# Check status
pandasync status
```

### Python API

```python
import pandasync

# Create and start a device
device = pandasync.Device(
    name="MyRecorder",
    channels=8,
)
device.start()

# Discover other devices
devices = device.discover()

# Connect audio
device.connect(
    source="Mic Array:ch1-8",
    destination="MyRecorder:ch1-8",
)
```

## Development

```bash
cd sdks/python
uv sync --dev
uv run pytest
uv run ruff check src/ tests/
uv run mypy src/
```

## License

Apache 2.0
