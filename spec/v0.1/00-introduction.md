# PandaSync Protocol Specification v0.1 -- Introduction

**Status:** Draft

## Scope

This specification defines the PandaSync networked audio transport protocol. PandaSync enables zero-configuration audio routing over standard IP networks with broadcast-grade timing and an open, web-native control plane.

## Terminology

- **Device**: Any network endpoint that sends or receives audio using PandaSync.
- **Source**: An audio output from a device (one or more channels).
- **Receiver**: An audio input on a device (one or more channels).
- **Connection**: An active audio route between a source and a receiver.
- **Profile**: An operational mode (Simple, Broadcast, or Developer) that determines default behavior.

## Conformance

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this specification are to be interpreted as described in RFC 2119.

## Document Structure

- [Transport](01-transport.md)
- [Clock Sync](02-clock-sync.md)
- [Discovery](03-discovery.md)
- [Control Plane](04-control-plane.md)
- [API Reference](05-api-reference.md)
