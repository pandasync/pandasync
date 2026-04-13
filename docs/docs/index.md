# PandaSync

**Plug-in simplicity. Broadcast grade. Completely open.**

PandaSync is an open-source networked audio transport protocol designed for live sound, broadcast, install AV, and remote production.

## What is PandaSync?

PandaSync routes audio over standard IP networks with zero configuration. It provides:

- **Zero-config discovery** -- plug in a device, see it on the network
- **Broadcast-grade timing** -- sub-microsecond clock synchronization via IEEE 1588v2 PTP
- **Web-native control** -- every device serves a full routing UI from its own embedded web server
- **Transport flexibility** -- AES67-compatible RTP for LAN, QUIC for WAN, WebRTC for browsers
- **Three operational profiles** -- Simple, Broadcast, and Developer modes for different use cases
- **Open protocol and open source** -- Apache 2.0 licensed, no per-channel or per-device fees

## Quick Start

```bash
pip install pandasync
pandasync discover
pandasync connect "Mic:ch1" "Recorder:ch1"
```

See the [Getting Started](getting-started.md) guide for a full walkthrough.

## Architecture

PandaSync is organized in five layers:

| Layer | Responsibility |
|---|---|
| **Transport** | AES67 RTP/UDP, QUIC, WebRTC |
| **Clock Sync** | IEEE 1588v2 PTP with auto-configuration |
| **Discovery** | mDNS (LAN), unicast DNS-SD (facility), cloud registry (WAN) |
| **Control Plane** | REST API, WebSocket events, NMOS compatibility |
| **Applications** | Web UI, CLI, mobile apps |

See [Architecture](architecture.md) for the full design.
