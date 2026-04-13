# Python SDK

The PandaSync Python SDK provides a complete implementation of the PandaSync protocol for scripting, server applications, and rapid prototyping.

## Installation

```bash
pip install pandasync
```

## CLI Reference

### `pandasync discover`

Scan the network for PandaSync devices.

```bash
pandasync discover                    # Default: 3s timeout, mDNS
pandasync discover --timeout 10       # Longer scan
pandasync discover --tier mdns --tier dns_sd  # Multiple tiers
```

### `pandasync connect`

Route audio between devices.

```bash
pandasync connect "Mic:ch1" "Recorder:ch1"
pandasync connect "Mixer:out1-8" "Speaker:in1-8" --transport rtp
```

### `pandasync status`

Show device status.

```bash
pandasync status
pandasync status --watch    # Continuous updates
```

## Python API

### Device

The `Device` class is the main integration point:

```python
import pandasync

device = pandasync.Device(
    name="MyDevice",
    channels_in=8,
    channels_out=8,
    profile=pandasync.Profile.DEVELOPER,
)
device.start()
```

### Discovery

```python
devices = device.discover()
for d in devices:
    print(f"{d.name} at {d.host} ({d.channels_in}in/{d.channels_out}out)")
```

### Connections

```python
conn = device.connect("Source:ch1", "Dest:ch1")
device.disconnect(conn.id)
```

### Configuration

```python
from pandasync.config import Config
from pandasync.profiles import Profile

config = Config.for_profile(Profile.BROADCAST, channels_in=32)
```

## REST API

Start the built-in API server:

```python
from pandasync.control.api import create_app
import uvicorn

app = create_app()
uvicorn.run(app, host="0.0.0.0", port=9820)
```

Then visit `http://localhost:9820/api/docs` for interactive API documentation.
