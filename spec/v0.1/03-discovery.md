# Discovery

**Status:** Draft

## Overview

PandaSync uses a three-tier discovery mechanism so devices can be found across any network topology.

## Tier 1 -- mDNS/DNS-SD

- Service type: `_pandasync._udp`
- Devices MUST register via mDNS on startup.
- TXT record properties:
  - `version` -- protocol version
  - `channels_in` -- number of input channels
  - `channels_out` -- number of output channels
  - `profile` -- operational profile (simple, broadcast, developer)

## Tier 2 -- Unicast DNS-SD

- Devices MAY register with a unicast DNS-SD server for cross-subnet discovery.
- One registry per facility.
- *Detailed specification to follow.*

## Tier 3 -- Cloud Registry

- Devices MAY register with an optional cloud registry for WAN discovery.
- *Detailed specification to follow.*

## Deduplication

When a device is discovered via multiple tiers, implementations MUST deduplicate based on the device's host address and port.

## Fallback

Devices MUST attempt all configured tiers and present a unified view of discovered devices.
