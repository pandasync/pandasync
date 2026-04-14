"""Stream manager -- tracks active RTP senders and receivers on a Device."""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID, uuid4

from pandasync.transport.rtp import RTPConfig, RTPReceiver, RTPSender

logger = logging.getLogger(__name__)

# RTP convention uses even ports starting at 5004
DEFAULT_BASE_PORT = 5004
PORT_RANGE = 1000  # 5004..6004


@dataclass
class Stream:
    """A tracked audio stream (sender or receiver)."""

    stream_id: UUID
    role: str  # "sender" or "receiver"
    source_desc: str
    sender: RTPSender | None = None
    receiver: RTPReceiver | None = None
    dest_host: str | None = None
    dest_port: int | None = None
    local_port: int | None = None


@dataclass
class StreamManager:
    """Manages the lifecycle of all RTP streams on this device."""

    base_port: int = DEFAULT_BASE_PORT
    _streams: dict[UUID, Stream] = field(default_factory=dict)
    _used_ports: set[int] = field(default_factory=set)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def create_receiver(
        self,
        source_desc: str,
        config: RTPConfig | None = None,
    ) -> tuple[UUID, int]:
        """Create and start a new RTP receiver.

        Args:
            source_desc: Human-readable source identifier (e.g., "Mic:ch1").
            config: Optional RTP configuration. Port is overridden.

        Returns:
            Tuple of (stream_id, bound_port).
        """
        with self._lock:
            port = self._allocate_port()
            stream_id = uuid4()

            receiver = RTPReceiver(port=port, config=config)
            receiver.start()

            stream = Stream(
                stream_id=stream_id,
                role="receiver",
                source_desc=source_desc,
                receiver=receiver,
                local_port=port,
            )
            self._streams[stream_id] = stream

        logger.info(
            "Created receiver stream %s for '%s' on port %d",
            stream_id,
            source_desc,
            port,
        )
        return stream_id, port

    def create_sender(
        self,
        source_desc: str,
        dest_host: str,
        dest_port: int,
        stream_id: UUID | None = None,
        config: RTPConfig | None = None,
    ) -> UUID:
        """Create and start a new RTP sender.

        Args:
            source_desc: Human-readable source identifier.
            dest_host: Destination IP or hostname.
            dest_port: Destination UDP port.
            stream_id: Optional pre-assigned stream ID.
            config: Optional RTP configuration (verification, drop rate, etc.)

        Returns:
            The stream_id.
        """
        with self._lock:
            sid = stream_id or uuid4()
            sender = RTPSender(
                dest_host=dest_host,
                dest_port=dest_port,
                config=config,
            )
            sender.start()

            stream = Stream(
                stream_id=sid,
                role="sender",
                source_desc=source_desc,
                sender=sender,
                dest_host=dest_host,
                dest_port=dest_port,
            )
            self._streams[sid] = stream

        logger.info(
            "Created sender stream %s for '%s' → %s:%d",
            sid,
            source_desc,
            dest_host,
            dest_port,
        )
        return sid

    def stop_stream(self, stream_id: UUID) -> bool:
        """Stop and remove a stream by ID.

        Returns True if the stream existed and was stopped.
        """
        with self._lock:
            stream = self._streams.pop(stream_id, None)
            if stream is None:
                return False

            if stream.sender is not None:
                stream.sender.stop()
            if stream.receiver is not None:
                stream.receiver.stop()
                if stream.local_port is not None:
                    self._used_ports.discard(stream.local_port)

        logger.info("Stopped stream %s", stream_id)
        return True

    def stop_all(self) -> None:
        """Stop all active streams."""
        with self._lock:
            stream_ids = list(self._streams.keys())

        for sid in stream_ids:
            self.stop_stream(sid)

    def get_stats(self) -> list[dict[str, Any]]:
        """Return statistics for all active streams."""
        with self._lock:
            streams = list(self._streams.values())

        stats: list[dict[str, Any]] = []
        for stream in streams:
            base: dict[str, Any] = {
                "stream_id": str(stream.stream_id),
                "role": stream.role,
                "source_desc": stream.source_desc,
            }
            if stream.sender is not None:
                base.update(stream.sender.stats())
            if stream.receiver is not None:
                base.update(stream.receiver.stats())
            stats.append(base)
        return stats

    def get_stream(self, stream_id: UUID) -> Stream | None:
        """Look up a stream by ID."""
        with self._lock:
            return self._streams.get(stream_id)

    def _allocate_port(self) -> int:
        """Allocate the next even UDP port for an RTP stream."""
        port = self.base_port
        while port < self.base_port + PORT_RANGE:
            if port not in self._used_ports:
                self._used_ports.add(port)
                return port
            port += 2  # RTP uses even ports; odd reserved for RTCP
        raise RuntimeError("No free RTP ports available")
