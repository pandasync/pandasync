"""AES67-compatible RTP transport.

Handles sending and receiving audio streams over RTP/UDP.
Phase 2: threaded sender (test tone generator) and receiver (packet counter).
Production audio transport with real I/O will be wired later.
"""

from __future__ import annotations

import logging
import math
import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class RTPConfig:
    """Configuration for an RTP stream."""

    port: int = 5004
    payload_type: int = 97  # dynamic, L24/48000
    sample_rate: int = 48000
    channels: int = 1
    bit_depth: int = 24
    packet_time_ms: float = 1.0  # 1ms packets per AES67
    tone_frequency_hz: float = 440.0  # Test tone: A4


def _build_rtp_header(
    sequence: int,
    timestamp: int,
    ssrc: int,
    payload_type: int,
) -> bytes:
    """Build a 12-byte RTP header."""
    byte0 = 0x80  # V=2, P=0, X=0, CC=0
    byte1 = payload_type & 0x7F
    return struct.pack(
        "!BBHII",
        byte0,
        byte1,
        sequence & 0xFFFF,
        timestamp & 0xFFFFFFFF,
        ssrc & 0xFFFFFFFF,
    )


def _generate_tone_samples(
    count: int,
    phase: float,
    frequency_hz: float,
    sample_rate: int,
    bit_depth: int,
) -> tuple[bytes, float]:
    """Generate PCM samples for a sine wave.

    Returns (bytes, new_phase). bit_depth must be 16 or 24.
    """
    two_pi = 2.0 * math.pi
    phase_increment = two_pi * frequency_hz / sample_rate

    if bit_depth == 24:
        max_val = 0x7FFFFF
        buf = bytearray()
        for _ in range(count):
            sample = int(math.sin(phase) * max_val * 0.5)  # -6dB headroom
            # Pack as 24-bit big-endian (AES67 network byte order)
            if sample < 0:
                sample += 0x1000000
            buf.append((sample >> 16) & 0xFF)
            buf.append((sample >> 8) & 0xFF)
            buf.append(sample & 0xFF)
            phase += phase_increment
            if phase >= two_pi:
                phase -= two_pi
        return bytes(buf), phase
    elif bit_depth == 16:
        max_val = 0x7FFF
        buf = bytearray()
        for _ in range(count):
            sample = int(math.sin(phase) * max_val * 0.5)
            buf.extend(struct.pack("!h", sample))
            phase += phase_increment
            if phase >= two_pi:
                phase -= two_pi
        return bytes(buf), phase
    else:
        raise ValueError(f"Unsupported bit_depth: {bit_depth}")


class RTPSender:
    """Sends AES67-compatible RTP audio packets in a background thread.

    Generates a sine wave test tone as the audio source. Real audio input
    (ALSA, I2S) will be wired later.
    """

    def __init__(
        self,
        dest_host: str,
        dest_port: int,
        config: RTPConfig | None = None,
    ) -> None:
        self.config = config or RTPConfig()
        self.dest_host = dest_host
        self.dest_port = dest_port

        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._sequence = 0
        self._timestamp = 0
        self._ssrc = id(self) & 0xFFFFFFFF

        self._packets_sent = 0
        self._bytes_sent = 0
        self._started_at: float | None = None

    def start(self) -> None:
        """Start the sender in a background thread."""
        if self._thread is not None:
            return

        self._socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP,
        )
        self._stop_event.clear()
        self._started_at = time.monotonic()
        self._thread = threading.Thread(
            target=self._run,
            name=f"rtp-sender-{self.dest_host}:{self.dest_port}",
            daemon=True,
        )
        self._thread.start()
        logger.info(
            "RTPSender started → %s:%d",
            self.dest_host,
            self.dest_port,
        )

    def stop(self) -> None:
        """Stop the sender thread and close the socket."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        logger.info("RTPSender stopped (%d packets sent)", self._packets_sent)

    def stats(self) -> dict[str, Any]:
        """Return current sender statistics."""
        uptime = (
            time.monotonic() - self._started_at if self._started_at is not None else 0.0
        )
        return {
            "role": "sender",
            "dest_host": self.dest_host,
            "dest_port": self.dest_port,
            "packets_sent": self._packets_sent,
            "bytes_sent": self._bytes_sent,
            "uptime_seconds": uptime,
            "packets_per_second": (self._packets_sent / uptime if uptime > 0 else 0.0),
        }

    def _run(self) -> None:
        """Sender thread: generate tone, pack into RTP, send, pace to real time."""
        cfg = self.config
        samples_per_packet = int(cfg.sample_rate * cfg.packet_time_ms / 1000)
        packet_interval_s = cfg.packet_time_ms / 1000.0
        bytes_per_sample = cfg.bit_depth // 8

        phase = 0.0
        next_send = time.monotonic()

        while not self._stop_event.is_set():
            # Generate audio for this packet (mono test tone)
            audio_data, phase = _generate_tone_samples(
                samples_per_packet * cfg.channels,
                phase,
                cfg.tone_frequency_hz,
                cfg.sample_rate,
                cfg.bit_depth,
            )

            header = _build_rtp_header(
                self._sequence,
                self._timestamp,
                self._ssrc,
                cfg.payload_type,
            )
            packet = header + audio_data

            try:
                assert self._socket is not None
                self._socket.sendto(packet, (self.dest_host, self.dest_port))
                self._packets_sent += 1
                self._bytes_sent += len(packet)
            except OSError as e:
                logger.warning("RTPSender send failed: %s", e)

            self._sequence = (self._sequence + 1) & 0xFFFF
            self._timestamp = (self._timestamp + samples_per_packet) & 0xFFFFFFFF

            # Pace to real time
            next_send += packet_interval_s
            now = time.monotonic()
            sleep_for = next_send - now
            if sleep_for > 0:
                self._stop_event.wait(sleep_for)
            elif sleep_for < -0.1:
                # Fell behind by more than 100ms; resync
                next_send = now

            _ = bytes_per_sample  # used for docs, keep ref


class RTPReceiver:
    """Receives AES67-compatible RTP audio packets in a background thread.

    Tracks packet counts, byte counts, sequence gaps, and timestamps.
    Real audio output (ALSA, I2S) will be wired later.
    """

    def __init__(
        self,
        port: int,
        config: RTPConfig | None = None,
    ) -> None:
        self.config = config or RTPConfig(port=port)
        self.port = port

        self._socket: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

        self._packets_received = 0
        self._bytes_received = 0
        self._last_packet_at: float | None = None
        self._started_at: float | None = None
        self._last_sequence: int | None = None
        self._sequence_gaps = 0
        self._peer: tuple[str, int] | None = None

    def start(self) -> None:
        """Bind the UDP socket and start the receive thread."""
        if self._thread is not None:
            return

        self._socket = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP,
        )
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(("", self.port))
        self._socket.settimeout(0.5)
        self._stop_event.clear()
        self._started_at = time.monotonic()
        self._thread = threading.Thread(
            target=self._run,
            name=f"rtp-receiver-{self.port}",
            daemon=True,
        )
        self._thread.start()
        logger.info("RTPReceiver started on port %d", self.port)

    def stop(self) -> None:
        """Stop the receive thread and close the socket."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        logger.info(
            "RTPReceiver stopped (%d packets received)",
            self._packets_received,
        )

    def stats(self) -> dict[str, Any]:
        """Return current receiver statistics."""
        uptime = (
            time.monotonic() - self._started_at if self._started_at is not None else 0.0
        )
        return {
            "role": "receiver",
            "port": self.port,
            "peer_host": self._peer[0] if self._peer else None,
            "peer_port": self._peer[1] if self._peer else None,
            "packets_received": self._packets_received,
            "bytes_received": self._bytes_received,
            "sequence_gaps": self._sequence_gaps,
            "uptime_seconds": uptime,
            "packets_per_second": (
                self._packets_received / uptime if uptime > 0 else 0.0
            ),
            "last_packet_age_s": (
                time.monotonic() - self._last_packet_at
                if self._last_packet_at is not None
                else None
            ),
        }

    def _run(self) -> None:
        """Receive thread: recv, parse RTP header, count."""
        while not self._stop_event.is_set():
            try:
                assert self._socket is not None
                data, addr = self._socket.recvfrom(65535)
            except TimeoutError:
                continue
            except OSError:
                break

            if len(data) < 12:
                continue

            # Parse RTP header
            try:
                _, _, seq, _, _ = struct.unpack("!BBHII", data[:12])
            except struct.error:
                continue

            self._packets_received += 1
            self._bytes_received += len(data)
            self._last_packet_at = time.monotonic()
            self._peer = addr

            # Track sequence gaps (wraps are expected every 65536 packets)
            if self._last_sequence is not None:
                expected = (self._last_sequence + 1) & 0xFFFF
                if seq != expected:
                    # Ignore wrap-around, only count real gaps
                    diff = (seq - expected) & 0xFFFF
                    if 0 < diff < 32768:
                        self._sequence_gaps += diff
            self._last_sequence = seq
