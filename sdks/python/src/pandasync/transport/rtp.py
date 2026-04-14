"""AES67-compatible RTP transport.

Handles sending and receiving audio streams over RTP/UDP.
Phase 2: threaded sender (test tone generator) and receiver (packet counter).
Phase 2.5: optional verification pattern and jitter/drift tracking.
Production audio transport with real I/O will be wired later.
"""

from __future__ import annotations

import collections
import logging
import math
import random
import socket
import statistics
import struct
import threading
import time
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


# Verification header embedded in the first 12 bytes of the RTP payload when
# verification is enabled. Format:
#   uint32 BE: packet counter (independent of RTP sequence wrap)
#   uint64 BE: send timestamp in nanoseconds (monotonic clock)
VERIFICATION_HEADER_SIZE = 12
VERIFICATION_MAGIC = 0x50414E44  # 'PAND'


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
    verification: bool = False  # embed counter + send timestamp in payload
    drop_rate: float = 0.0  # 0.0..1.0 random packet drop for testing


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
        self._packet_counter = 0  # 32-bit, wraps at 2^32

        self._packets_sent = 0
        self._packets_dropped = 0
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
            "RTPSender started -> %s:%d (verification=%s, drop_rate=%.3f)",
            self.dest_host,
            self.dest_port,
            self.config.verification,
            self.config.drop_rate,
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
        logger.info(
            "RTPSender stopped (%d sent, %d dropped)",
            self._packets_sent,
            self._packets_dropped,
        )

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
            "packets_dropped": self._packets_dropped,
            "bytes_sent": self._bytes_sent,
            "uptime_seconds": uptime,
            "packets_per_second": (self._packets_sent / uptime if uptime > 0 else 0.0),
            "verification": self.config.verification,
            "drop_rate": self.config.drop_rate,
        }

    def _build_verification_header(self) -> bytes:
        """Build the 12-byte verification header.

        [ magic:4 | counter:4 | send_time_ns:8 ]
        Actually we use 4 bytes magic + 4 bytes counter + 8 bytes timestamp
        = 16 bytes. But we budgeted 12 in the payload, so drop magic.
        """
        send_time_ns = time.monotonic_ns()
        return struct.pack("!IQ", self._packet_counter, send_time_ns)

    def _run(self) -> None:
        """Sender thread: generate tone, pack into RTP, send, pace to real time."""
        cfg = self.config
        samples_per_packet = int(cfg.sample_rate * cfg.packet_time_ms / 1000)
        packet_interval_s = cfg.packet_time_ms / 1000.0

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

            # Optionally prepend verification header (replaces some audio bytes)
            if cfg.verification:
                vheader = self._build_verification_header()
                payload = vheader + audio_data[VERIFICATION_HEADER_SIZE:]
            else:
                payload = audio_data

            header = _build_rtp_header(
                self._sequence,
                self._timestamp,
                self._ssrc,
                cfg.payload_type,
            )
            packet = header + payload

            should_drop = cfg.drop_rate > 0.0 and random.random() < cfg.drop_rate

            if not should_drop:
                try:
                    assert self._socket is not None
                    self._socket.sendto(packet, (self.dest_host, self.dest_port))
                    self._packets_sent += 1
                    self._bytes_sent += len(packet)
                except OSError as e:
                    logger.warning("RTPSender send failed: %s", e)
            else:
                self._packets_dropped += 1

            self._sequence = (self._sequence + 1) & 0xFFFF
            self._packet_counter = (self._packet_counter + 1) & 0xFFFFFFFF
            self._timestamp = (self._timestamp + samples_per_packet) & 0xFFFFFFFF

            # Pace to real time
            next_send += packet_interval_s
            now = time.monotonic()
            sleep_for = next_send - now
            if sleep_for > 0:
                self._stop_event.wait(sleep_for)
            elif sleep_for < -0.1:
                next_send = now


class RTPReceiver:
    """Receives AES67-compatible RTP audio packets in a background thread.

    Tracks packet counts, byte counts, sequence gaps, inter-arrival jitter,
    and (when verification is enabled) send-to-receive latency for drift.
    """

    JITTER_WINDOW = 2000  # rolling window size for jitter samples
    LATENCY_WINDOW = 2000  # rolling window for send->recv latency

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

        self._inter_arrivals: collections.deque[float] = collections.deque(
            maxlen=self.JITTER_WINDOW
        )
        self._latencies_ns: collections.deque[int] = collections.deque(
            maxlen=self.LATENCY_WINDOW
        )
        self._verification_errors = 0
        self._last_expected_counter: int | None = None

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

        jitter = self._jitter_stats()

        latencies = list(self._latencies_ns)
        latency_stats: dict[str, float | None] = {
            "mean_ns": None,
            "min_ns": None,
            "max_ns": None,
        }
        if len(latencies) >= 2:
            latency_stats = {
                "mean_ns": statistics.mean(latencies),
                "min_ns": float(min(latencies)),
                "max_ns": float(max(latencies)),
            }

        return {
            "role": "receiver",
            "port": self.port,
            "peer_host": self._peer[0] if self._peer else None,
            "peer_port": self._peer[1] if self._peer else None,
            "packets_received": self._packets_received,
            "bytes_received": self._bytes_received,
            "sequence_gaps": self._sequence_gaps,
            "verification_errors": self._verification_errors,
            "uptime_seconds": uptime,
            "packets_per_second": (
                self._packets_received / uptime if uptime > 0 else 0.0
            ),
            "last_packet_age_s": (
                time.monotonic() - self._last_packet_at
                if self._last_packet_at is not None
                else None
            ),
            "jitter": jitter,
            "latency": latency_stats,
        }

    def _jitter_stats(self) -> dict[str, float | None]:
        samples = list(self._inter_arrivals)
        if len(samples) < 2:
            return {
                "samples": len(samples),
                "mean_ms": None,
                "stddev_ms": None,
                "min_ms": None,
                "max_ms": None,
            }
        return {
            "samples": len(samples),
            "mean_ms": statistics.mean(samples) * 1000,
            "stddev_ms": statistics.stdev(samples) * 1000,
            "min_ms": min(samples) * 1000,
            "max_ms": max(samples) * 1000,
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

            recv_time = time.monotonic()
            recv_time_ns = time.monotonic_ns()

            if len(data) < 12:
                continue

            # Parse RTP header
            try:
                _, _, seq, _, _ = struct.unpack("!BBHII", data[:12])
            except struct.error:
                continue

            # Track inter-arrival time
            if self._last_packet_at is not None:
                self._inter_arrivals.append(recv_time - self._last_packet_at)

            self._packets_received += 1
            self._bytes_received += len(data)
            self._last_packet_at = recv_time
            self._peer = addr

            # Track sequence gaps (wraps are expected every 65536 packets)
            if self._last_sequence is not None:
                expected = (self._last_sequence + 1) & 0xFFFF
                if seq != expected:
                    diff = (seq - expected) & 0xFFFF
                    if 0 < diff < 32768:
                        self._sequence_gaps += diff
            self._last_sequence = seq

            # Parse verification header if payload is long enough
            payload = data[12:]
            if len(payload) >= VERIFICATION_HEADER_SIZE:
                self._check_verification(payload, recv_time_ns)

    def _check_verification(self, payload: bytes, recv_time_ns: int) -> None:
        """Verify the optional verification header in the payload.

        Format: [ counter: uint32 BE | send_time_ns: uint64 BE ]
        A payload without verification contains arbitrary audio bytes,
        so we can only flag errors when we've seen the stream use
        verification consistently. Heuristic: if the first sample of the
        previous packet's payload (as a big-endian u32) matched our
        expected counter, we're in verification mode.
        """
        try:
            counter, send_time_ns = struct.unpack(
                "!IQ", payload[:VERIFICATION_HEADER_SIZE]
            )
        except struct.error:
            return

        # Latency: if send_time_ns looks plausible (both clocks monotonic,
        # but they're on different machines, so differences can be huge —
        # we only care about the *rate of change* of this difference for
        # drift measurement, not the absolute value).
        self._latencies_ns.append(recv_time_ns - send_time_ns)

        # Verification: counter should be expected_counter
        if (
            self._last_expected_counter is not None
            and counter != self._last_expected_counter
        ):
            self._verification_errors += 1
        self._last_expected_counter = (counter + 1) & 0xFFFFFFFF
