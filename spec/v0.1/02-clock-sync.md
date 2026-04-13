# Clock Synchronization

**Status:** Draft

## Overview

PandaSync uses IEEE 1588v2 PTP for sub-microsecond clock synchronization between devices. Clock configuration is automatic; users SHOULD NOT need to configure PTP manually.

## PTP Profile

PandaSync devices MUST implement the AES67 media profile for PTP:

- PTP domain: 0 (default, configurable)
- Announce interval: 1 second
- Sync interval: 125 ms
- Transport: UDP over IPv4 (multicast)

## Auto-Configuration

1. On startup, a device MUST listen for PTP announce messages.
2. If an external grandmaster is detected, the device MUST synchronize to it.
3. If no external grandmaster is present, devices MUST run the Best Master Clock Algorithm (BMCA) to elect a grandmaster.
4. Devices SHOULD monitor clock health and re-elect on grandmaster failure.

## Clock Status

Each device MUST report its clock status as one of:

- `locked` -- synchronized to grandmaster, offset < 1 us
- `locking` -- synchronization in progress
- `free_run` -- no synchronization available
- `unknown` -- status not yet determined

## NTP Fallback

For WAN and cloud scenarios where PTP is not available, devices MAY use NTP with software clock disciplining. NTP-synchronized streams are suitable for monitoring but SHOULD NOT be used for broadcast-grade applications.
