# PandaSync

**Plug-in simplicity. Broadcast grade. Completely open.**

PandaSync is an open-source networked audio transport protocol designed for live sound, broadcast, install AV, and remote production. It provides zero-configuration audio routing with broadcast-grade timing, a web-native control plane, and a developer-first ecosystem.

## Architecture

PandaSync is organized in five layers, each with a single responsibility and sensible defaults:

```
+--------------------------------------------------------------+
|                    LAYER 5 -- APPLICATIONS                   |
|   Web Controller  |  Mobile App  |  REST API  |  CLI Tools   |
+--------------------------------------------------------------+
|                    LAYER 4 -- CONTROL PLANE                  |
|   Device Registry  |  Routing Engine  |  Multicast Manager   |
|   REST API + WebSocket events                                |
+--------------------------------------------------------------+
|                    LAYER 3 -- DISCOVERY                       |
|   mDNS/DNS-SD (zero-config LAN)                             |
|   + Unicast DNS-SD (cross-subnet / facility)                 |
|   + Cloud registry (WAN / multi-site)                        |
+--------------------------------------------------------------+
|                    LAYER 2 -- CLOCK SYNC                     |
|   IEEE 1588v2 PTP (auto-configured)                          |
|   + NTP fallback for WAN/cloud                               |
+--------------------------------------------------------------+
|                    LAYER 1 -- TRANSPORT                       |
|   AES67 RTP/UDP (primary)                                    |
|   + QUIC (WAN / lossy networks)                              |
|   + WebRTC (browser / cloud)                                 |
+--------------------------------------------------------------+
```

## Quick Start

### Install the Python SDK

```bash
pip install pandasync
```

### Discover devices on your network

```bash
pandasync discover
```

### Route audio between two devices

```bash
pandasync connect "Mic Array:ch1-8" "Recorder:ch1-8"
```

### Check status

```bash
pandasync status
```

## Operational Profiles

PandaSync supports three operational profiles. The same protocol underneath -- the profile changes only what the UI exposes:

- **Simple** -- Zero-config, auto-clock, GUI-only. Plug in, open a browser, route audio.
- **Broadcast** -- Full NMOS IS-04/05, external PTP, SDP import/export, ST 2110-30 compliance.
- **Developer** -- Full REST API, WebSocket events, CLI, declarative routing, metrics.

## Repository Layout

```
spec/           Protocol specification
sdks/python/    Python SDK
controller/     Web controller (coming soon)
hardware/       Hardware bridge designs (coming soon)
docs/           Documentation site
```

## SDKs

| SDK | Language | Status |
|---|---|---|
| `pandasync` (Python) | Python 3.11+ | In development |
| `libpandasync` (C/C++) | C / C++ | Planned |
| `pandasync-js` (TypeScript) | TypeScript / JS | Planned |
| `pandasync-go` (Go) | Go | Planned |

## REST API

Every PandaSync device exposes a complete REST API:

```http
GET  /api/v1/devices         # List all discovered devices
GET  /api/v1/sources         # Available audio sources
GET  /api/v1/receivers       # Available receivers
POST /api/v1/connect         # Make a connection
POST /api/v1/disconnect      # Break a connection
GET  /api/v1/status          # Clock sync, latency, levels
WS   /api/v1/events          # Real-time status stream
```

Interactive API docs are available at `/api/docs` on every device.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

Apache 2.0 -- see [LICENSE](LICENSE) for details.
