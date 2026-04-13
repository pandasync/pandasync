"""AES67-compatible RTP transport.

Handles sending and receiving audio streams over RTP/UDP.
Phase 0: basic RTP sender/receiver for demo purposes.
Production audio transport will use the C SDK or native extensions.
"""

from __future__ import annotations

import socket
import struct
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class RTPConfig:
    """Configuration for an RTP stream."""

    multicast_group: str = "239.69.0.1"
    port: int = 5004
    payload_type: int = 97  # dynamic, L24/48000
    sample_rate: int = 48000
    channels: int = 2
    bit_depth: int = 24
    packet_time_ms: float = 1.0  # 1ms packets per AES67


@dataclass
class RTPSender:
    """Sends audio data as AES67-compatible RTP packets."""

    config: RTPConfig = field(default_factory=RTPConfig)
    _socket: socket.socket | None = None
    _sequence: int = 0
    _timestamp: int = 0
    _ssrc: int = 0

    def start(self) -> None:
        """Start the RTP sender."""
        self._socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP,
        )
        self._socket.setsockopt(
            socket.IPPROTO_IP,
            socket.IP_MULTICAST_TTL,
            2,
        )
        self._ssrc = id(self) & 0xFFFFFFFF

    def stop(self) -> None:
        """Stop the RTP sender."""
        if self._socket:
            self._socket.close()
            self._socket = None

    def send_packet(self, audio_data: bytes) -> None:
        """Send a single RTP packet with audio data."""
        if not self._socket:
            return

        header = self._build_header()
        packet = header + audio_data
        self._socket.sendto(packet, (self.config.multicast_group, self.config.port))

        self._sequence = (self._sequence + 1) & 0xFFFF
        samples_per_packet = int(
            self.config.sample_rate * self.config.packet_time_ms / 1000,
        )
        self._timestamp = (self._timestamp + samples_per_packet) & 0xFFFFFFFF

    def _build_header(self) -> bytes:
        """Build an RTP header (12 bytes)."""
        # V=2, P=0, X=0, CC=0, M=0
        byte0 = 0x80
        byte1 = self.config.payload_type & 0x7F
        return struct.pack(
            "!BBHII",
            byte0,
            byte1,
            self._sequence,
            self._timestamp,
            self._ssrc,
        )


@dataclass
class RTPReceiver:
    """Receives AES67-compatible RTP audio packets."""

    config: RTPConfig = field(default_factory=RTPConfig)
    on_audio: Callable[[bytes, int], None] | None = None
    _socket: socket.socket | None = None
    _running: bool = False

    def start(self) -> None:
        """Start the RTP receiver."""
        self._socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP,
        )
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("", self.config.port))

        # Join multicast group
        group = socket.inet_aton(self.config.multicast_group)
        mreq = struct.pack("4sL", group, socket.INADDR_ANY)
        self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self._running = True

    def stop(self) -> None:
        """Stop the RTP receiver."""
        self._running = False
        if self._socket:
            self._socket.close()
            self._socket = None

    def receive_packet(self) -> tuple[bytes, int] | None:
        """Receive a single RTP packet. Returns (audio_data, timestamp) or None."""
        if not self._socket or not self._running:
            return None

        try:
            data, _ = self._socket.recvfrom(65535)
        except OSError:
            return None

        if len(data) < 12:
            return None

        # Parse RTP header
        _, _, _, timestamp, _ = struct.unpack("!BBHII", data[:12])
        audio_data = data[12:]

        if self.on_audio:
            self.on_audio(audio_data, timestamp)

        return audio_data, timestamp
