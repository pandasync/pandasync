# Transport Layer

**Status:** Draft

## Overview

PandaSync supports three transport mechanisms. The primary transport is AES67-compatible RTP/UDP. Extensions provide QUIC for WAN scenarios and WebRTC for browser-based endpoints.

## RTP Transport (Primary)

### Wire Format

PandaSync RTP streams MUST conform to the AES67 standard:

- **Payload**: Linear PCM (L16 or L24)
- **Sample rates**: 44100, 48000, or 96000 Hz
- **Packet time**: 1 ms (48 samples at 48 kHz) as the default; 125 us and 4 ms also supported
- **RTP payload type**: Dynamic (negotiated via SDP or REST API)
- **Multicast**: 239.69.0.0/16 range (configurable)

### Packet Structure

Standard RTP header (RFC 3550) followed by PCM audio samples in network byte order (big-endian).

## QUIC Transport (Extension)

*To be specified in a future revision.*

## WebRTC Transport (Extension)

*To be specified in a future revision.*
