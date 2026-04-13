# API Reference

**Status:** Draft

## Data Models

### DeviceInfo

```json
{
  "id": "uuid",
  "name": "string",
  "host": "string",
  "port": 9820,
  "channels_in": 0,
  "channels_out": 0,
  "clock_status": "locked | locking | free_run | unknown",
  "clock_role": "grandmaster | boundary | slave | listener",
  "profile": "simple | broadcast | developer",
  "version": "string"
}
```

### AudioSource

```json
{
  "id": "uuid",
  "device_id": "uuid",
  "name": "string",
  "channels": 2,
  "sample_rate": 48000,
  "bit_depth": 24
}
```

### Receiver

```json
{
  "id": "uuid",
  "device_id": "uuid",
  "name": "string",
  "channels": 2,
  "sample_rate": 48000,
  "bit_depth": 24
}
```

### Connection

```json
{
  "id": "uuid",
  "source_id": "uuid",
  "receiver_id": "uuid",
  "transport": "auto | rtp | quic | webrtc",
  "active": true,
  "latency_ms": 0.0
}
```

## POST /api/v1/connect

### Request

```json
{
  "source": "DeviceName:channels",
  "destination": "DeviceName:channels",
  "transport": "auto"
}
```

### Response

```json
{
  "connection_id": "uuid",
  "source": "DeviceName:channels",
  "destination": "DeviceName:channels",
  "transport": "rtp",
  "status": "connected"
}
```

## POST /api/v1/disconnect

### Request

```json
{
  "connection_id": "uuid"
}
```

### Response

```json
{
  "connection_id": "uuid",
  "status": "disconnected"
}
```

## GET /api/v1/status

### Response

```json
{
  "version": "0.1.0",
  "clock_status": "locked",
  "clock_role": "slave",
  "clock_offset_us": 0.5,
  "active_connections": 3,
  "uptime_seconds": 3600.0
}
```
