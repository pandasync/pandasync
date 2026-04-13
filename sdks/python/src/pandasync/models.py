"""Core domain models for PandaSync."""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ClockStatus(StrEnum):
    """Clock synchronization status."""

    LOCKED = "locked"
    LOCKING = "locking"
    FREE_RUN = "free_run"
    UNKNOWN = "unknown"


class ClockRole(StrEnum):
    """Role in the PTP clock hierarchy."""

    GRANDMASTER = "grandmaster"
    BOUNDARY = "boundary"
    SLAVE = "slave"
    LISTENER = "listener"


class TransportType(StrEnum):
    """Available transport types."""

    AUTO = "auto"
    RTP = "rtp"
    QUIC = "quic"
    WEBRTC = "webrtc"


class DeviceInfo(BaseModel):
    """Information about a discovered PandaSync device."""

    id: UUID = Field(default_factory=uuid4)
    name: str
    host: str
    port: int = 9820
    channels_in: int = 0
    channels_out: int = 0
    clock_status: ClockStatus = ClockStatus.UNKNOWN
    clock_role: ClockRole = ClockRole.LISTENER
    profile: str = "simple"
    version: str = ""


class AudioSource(BaseModel):
    """An available audio source (output) on a device."""

    id: UUID = Field(default_factory=uuid4)
    device_id: UUID
    name: str
    channels: int
    sample_rate: int = 48000
    bit_depth: int = 24


class Receiver(BaseModel):
    """An available audio receiver (input) on a device."""

    id: UUID = Field(default_factory=uuid4)
    device_id: UUID
    name: str
    channels: int
    sample_rate: int = 48000
    bit_depth: int = 24


class Connection(BaseModel):
    """An active audio connection between a source and a receiver."""

    id: UUID = Field(default_factory=uuid4)
    source_id: UUID
    receiver_id: UUID
    transport: TransportType = TransportType.AUTO
    active: bool = True
    latency_ms: float = 0.0


class DeviceStatus(BaseModel):
    """Current status of a PandaSync device."""

    device: DeviceInfo
    clock_status: ClockStatus = ClockStatus.UNKNOWN
    clock_offset_us: float = 0.0
    active_connections: int = 0
    uptime_seconds: float = 0.0
