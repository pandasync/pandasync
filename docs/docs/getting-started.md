# Getting Started

Get PandaSync running between two machines in under five minutes.

## Prerequisites

- Python 3.11 or later
- Two machines on the same network (or one machine for testing)

## Install

```bash
pip install pandasync
```

## Discover Devices

Scan your local network for PandaSync devices:

```bash
pandasync discover
```

This uses mDNS to find devices on the same subnet. You'll see a table of discovered devices with their names, addresses, and channel counts.

## Route Audio

Connect a source to a receiver:

```bash
pandasync connect "SourceDevice:ch1" "ReceiverDevice:ch1"
```

The protocol auto-selects the best transport (RTP on LAN, QUIC over WAN).

## Check Status

View the current device status:

```bash
pandasync status
```

## Use the REST API

Every PandaSync device exposes a REST API. Open your browser to:

```
http://<device-ip>:9820/api/docs
```

This gives you an interactive API explorer (Swagger UI) where you can list devices, create connections, and monitor status.

## Python API

```python
import pandasync

device = pandasync.Device(
    name="MyDevice",
    channels_in=2,
    channels_out=2,
)
device.start()

# Discover other devices
devices = device.discover()
print(f"Found {len(devices)} devices")

# Create a connection
device.connect("Source:ch1", "MyDevice:in1")
```

## Next Steps

- Read the [Architecture](architecture.md) overview
- Explore the [Python SDK](sdk/python.md) reference
- Check the [REST API docs](/api/docs) on any running device
