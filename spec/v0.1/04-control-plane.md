# Control Plane

**Status:** Draft

## Overview

Every PandaSync device MUST expose a REST API and MAY expose a WebSocket event stream. No central controller is required; every device is a first-class participant.

## REST API

The API is versioned in the URL path. The current version is `v1`.

Base URL: `http://<device>:<port>/api/v1/`

### Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/devices` | List all discovered devices |
| GET | `/sources` | List available audio sources |
| GET | `/receivers` | List available audio receivers |
| POST | `/connect` | Create an audio connection |
| POST | `/disconnect` | Remove an audio connection |
| GET | `/status` | Device and clock status |
| WS | `/events` | Real-time event stream |

### Content Type

All requests and responses use `application/json`.

## WebSocket Events

The `/events` endpoint provides real-time notifications for:

- Device discovery and removal
- Connection state changes
- Clock status changes
- Error conditions

## NMOS Compatibility

PandaSync devices operating in Broadcast profile SHOULD implement NMOS IS-04 (discovery/registration) and IS-05 (connection management) so that existing broadcast tooling can interoperate.

## Authentication

- **Simple profile**: Bearer token authentication (optional)
- **Broadcast profile**: mTLS required
- **Developer profile**: Bearer token or mTLS
