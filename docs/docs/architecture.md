# Architecture

PandaSync is organized in five layers. Each layer has a single responsibility, a clear interface, and sensible defaults.

```
+--------------------------------------------------------------+
|                    LAYER 5 -- APPLICATIONS                   |
|   Web Controller  |  Mobile App  |  REST API  |  CLI Tools   |
+--------------------------------------------------------------+
|                    LAYER 4 -- CONTROL PLANE                  |
|   Device Registry  |  Routing Engine  |  Multicast Manager   |
+--------------------------------------------------------------+
|                    LAYER 3 -- DISCOVERY                       |
|   mDNS/DNS-SD  |  Unicast DNS-SD  |  Cloud Registry          |
+--------------------------------------------------------------+
|                    LAYER 2 -- CLOCK SYNC                     |
|   IEEE 1588v2 PTP  |  NTP Fallback                           |
+--------------------------------------------------------------+
|                    LAYER 1 -- TRANSPORT                       |
|   AES67 RTP/UDP  |  QUIC  |  WebRTC                          |
+--------------------------------------------------------------+
```

## Layer 1 -- Transport

The primary transport is AES67-compatible RTP/UDP with L16/L24 PCM at 44.1/48/96 kHz. Every PandaSync stream is, by construction, a valid AES67 stream receivable by any AES67-compatible device.

Extensions:

- **QUIC** for WAN and lossy networks, providing stream multiplexing, FEC, and NAT traversal.
- **WebRTC** for browser-based monitoring and cloud bridges.

Transport selection is automatic based on network topology.

## Layer 2 -- Clock Sync

PandaSync uses IEEE 1588v2 PTP for sub-microsecond clock synchronization. The clock hierarchy is auto-configured:

1. Detect external grandmaster (if present, sync to it)
2. Elect best device as grandmaster
3. Assign boundary and slave roles
4. Monitor health and re-elect on failure

Users never need to configure PTP manually. Clock status is visualized as green/yellow/red per device.

## Layer 3 -- Discovery

Three tiers stacked for any network topology:

- **Tier 1 -- mDNS/DNS-SD**: Zero-config LAN discovery
- **Tier 2 -- Unicast DNS-SD**: Cross-subnet, one registry per facility
- **Tier 3 -- Cloud Registry**: Optional, for WAN and multi-site workflows

Fallback is automatic. Each device tries all configured tiers and deduplicates.

## Layer 4 -- Control Plane

Every device exposes a REST API and WebSocket event stream:

```http
GET  /api/v1/devices
GET  /api/v1/sources
GET  /api/v1/receivers
POST /api/v1/connect
POST /api/v1/disconnect
GET  /api/v1/status
WS   /api/v1/events
```

No central controller is required. Every device is a first-class participant that knows the full network graph.

## Layer 5 -- Applications

- **Embedded web UI** on every device at `http://device.local:9820`
- **CLI tools**: `pandasync discover`, `pandasync connect`, `pandasync status`
- **REST API**: sufficient for building any custom controller
- **Mobile apps**: iOS and Android (planned)

## Operational Profiles

The same protocol supports three modes:

| | Simple | Broadcast | Developer |
|---|---|---|---|
| Discovery | mDNS | All tiers | All tiers |
| Latency | 2 ms | 1 ms | 1 ms |
| Clock | Auto | External GM | Auto |
| Auth | Optional | mTLS required | Bearer or mTLS |
| Metrics | Off | On | On |
