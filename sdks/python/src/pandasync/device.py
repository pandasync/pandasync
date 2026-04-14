"""PandaSync device -- the central integration class.

Wires together all five layers: transport, clock, discovery,
control plane, and applications. This is the main entry point
for embedding PandaSync in a product or application.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from pandasync._version import __version__
from pandasync.clock.manager import ClockManager
from pandasync.config import Config
from pandasync.discovery.manager import DiscoveryManager
from pandasync.exceptions import ConnectionError as PandaSyncConnectionError
from pandasync.models import (
    AudioSource,
    Connection,
    DeviceInfo,
    Receiver,
    TransportType,
)
from pandasync.profiles import Profile
from pandasync.transport.rtp import RTPConfig
from pandasync.transport.streams import StreamManager

logger = logging.getLogger(__name__)


@dataclass
class Device:
    """A PandaSync device.

    This is the top-level object that integrators use to add PandaSync
    to their product. It manages discovery, clock sync, transport,
    and the REST API server.

    Example::

        device = Device(name="MyMixer", channels_in=8, channels_out=8)
        device.start()
        devices = device.discover()
    """

    name: str = "PandaSync Device"
    channels_in: int = 2
    channels_out: int = 2
    profile: Profile = Profile.SIMPLE
    config: Config | None = None

    # Internal state
    _id: UUID = field(default_factory=uuid4)
    _discovery: DiscoveryManager | None = field(default=None, repr=False)
    _clock: ClockManager | None = field(default=None, repr=False)
    _streams: StreamManager = field(
        default_factory=StreamManager,
        repr=False,
    )
    _connections: list[Connection] = field(default_factory=list, repr=False)
    _remote_stream_map: dict[UUID, tuple[str, int, UUID]] = field(
        default_factory=dict,
        repr=False,
    )
    _running: bool = field(default=False, repr=False)
    _started_at: float | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.config is None:
            self.config = Config.for_profile(
                self.profile,
                device_name=self.name,
                channels_in=self.channels_in,
                channels_out=self.channels_out,
            )

    def start(self) -> None:
        """Start the device: discovery, clock sync, and control plane."""
        if self._running:
            return

        cfg = self.config
        assert cfg is not None

        # Start discovery
        self._discovery = DiscoveryManager(tiers=cfg.discovery_tiers)
        self._discovery.start()
        self._discovery.register(self.info)

        # Start clock
        self._clock = ClockManager()
        self._clock.auto_configure(self.discover())

        self._started_at = time.monotonic()
        self._running = True
        logger.info("Device '%s' started (profile=%s)", self.name, self.profile.value)

    def stop(self) -> None:
        """Stop the device and clean up resources."""
        if not self._running:
            return

        self._streams.stop_all()

        if self._discovery:
            self._discovery.unregister(self.info)
            self._discovery.stop()

        self._started_at = None
        self._running = False
        logger.info("Device '%s' stopped", self.name)

    def discover(self) -> list[DeviceInfo]:
        """Discover other PandaSync devices on the network."""
        if self._discovery:
            return self._discovery.discover()
        return []

    def connect(
        self,
        source: str,
        destination: str,
        transport: TransportType = TransportType.AUTO,
        verification: bool = False,
        drop_rate: float = 0.0,
    ) -> Connection:
        """Create an audio connection between a source and a receiver.

        This device acts as the sender. The destination is resolved via
        discovery, its /streams/receive endpoint is called to obtain a port,
        then a local RTP sender is started.

        Args:
            source: Source identifier (e.g., "MicArray:ch1").
            destination: Receiver identifier (e.g., "Recorder:ch1").
            transport: Transport type to use (default: auto-select).

        Returns:
            The created Connection object.
        """
        import httpx

        dest_device_name = destination.split(":", 1)[0]
        dest_device = self._find_device(dest_device_name)
        if dest_device is None:
            raise PandaSyncConnectionError(
                f"Destination device '{dest_device_name}' not found"
            )

        # Ask destination to prepare a receiver
        url = f"http://{dest_device.host}:{dest_device.port}/api/v1/streams/receive"
        try:
            resp = httpx.post(
                url,
                json={
                    "source": source,
                    "destination": destination,
                    "verification": verification,
                },
                timeout=5.0,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise PandaSyncConnectionError(
                f"Failed to prepare receiver on {dest_device.name}: {e}"
            ) from e

        remote_stream_id = UUID(data["stream_id"])
        remote_port = int(data["port"])

        # Start local sender targeting the remote receiver's port
        sender_config = RTPConfig(
            verification=verification,
            drop_rate=drop_rate,
        )
        local_stream_id = self._streams.create_sender(
            source_desc=f"{source}->{destination}",
            dest_host=dest_device.host,
            dest_port=remote_port,
            config=sender_config,
        )

        connection = Connection(
            id=local_stream_id,
            source_id=self._id,
            receiver_id=dest_device.id,
            transport=transport,
        )
        self._connections.append(connection)
        self._remote_stream_map[local_stream_id] = (
            dest_device.host,
            dest_device.port,
            remote_stream_id,
        )

        logger.info(
            "Connection %s: %s -> %s (via %s:%d)",
            local_stream_id,
            source,
            destination,
            dest_device.host,
            remote_port,
        )
        return connection

    def disconnect(self, connection_id: UUID) -> None:
        """Disconnect an active audio connection."""
        import httpx

        self._streams.stop_stream(connection_id)

        # Tell the remote side to stop its receiver
        remote = self._remote_stream_map.pop(connection_id, None)
        if remote is not None:
            host, port, remote_stream_id = remote
            url = f"http://{host}:{port}/api/v1/streams/stop"
            try:
                httpx.post(
                    url,
                    json={"stream_id": str(remote_stream_id)},
                    timeout=2.0,
                )
            except httpx.HTTPError as e:
                logger.warning(
                    "Failed to notify remote %s to stop stream: %s",
                    host,
                    e,
                )

        self._connections = [c for c in self._connections if c.id != connection_id]
        logger.info("Connection %s disconnected", connection_id)

    def prepare_receive(
        self,
        source: str,
        destination: str,
        verification: bool = False,
    ) -> tuple[UUID, int]:
        """Prepare an RTP receiver for an incoming stream.

        Called by the /streams/receive API endpoint. Returns the stream ID
        and port the remote sender should target.
        """
        receiver_config = RTPConfig(verification=verification)
        return self._streams.create_receiver(
            source_desc=f"{source}->{destination}",
            config=receiver_config,
        )

    def stop_stream(self, stream_id: UUID) -> bool:
        """Stop a stream by ID (used by API /streams/stop)."""
        return self._streams.stop_stream(stream_id)

    def _find_device(self, name: str) -> DeviceInfo | None:
        """Find a discovered device by name (including self)."""
        if name == self.name:
            return self.info
        for device in self.discover():
            if device.name == name:
                return device
        return None

    @property
    def info(self) -> DeviceInfo:
        """Return this device's info for discovery and API responses."""
        assert self.config is not None
        return DeviceInfo(
            id=self._id,
            name=self.name,
            host="0.0.0.0",
            port=self.config.api_port,
            channels_in=self.channels_in,
            channels_out=self.channels_out,
            profile=self.profile.value,
            version=__version__,
        )

    @property
    def sources(self) -> list[AudioSource]:
        """Return audio sources provided by this device."""
        assert self.config is not None
        return [
            AudioSource(
                device_id=self._id,
                name=f"{self.name}:out{i + 1}",
                channels=1,
                sample_rate=self.config.sample_rate,
                bit_depth=self.config.bit_depth,
            )
            for i in range(self.channels_out)
        ]

    @property
    def receivers(self) -> list[Receiver]:
        """Return audio receivers on this device."""
        assert self.config is not None
        return [
            Receiver(
                device_id=self._id,
                name=f"{self.name}:in{i + 1}",
                channels=1,
                sample_rate=self.config.sample_rate,
                bit_depth=self.config.bit_depth,
            )
            for i in range(self.channels_in)
        ]

    @property
    def connections(self) -> list[Connection]:
        """Return all active connections."""
        return list(self._connections)

    @property
    def streams(self) -> StreamManager:
        """Return the stream manager for direct access."""
        return self._streams

    @property
    def uptime_seconds(self) -> float:
        """Return seconds since the device was started."""
        if self._started_at is None:
            return 0.0
        return time.monotonic() - self._started_at

    def serve(
        self,
        host: str = "0.0.0.0",
        port: int | None = None,
    ) -> None:
        """Start the device and run the REST API server (blocking).

        Args:
            host: Bind address for the API server.
            port: Port for the API server. Defaults to config.api_port.
        """
        import uvicorn

        from pandasync.control.api import create_app

        if not self._running:
            self.start()

        app = create_app(device=self)
        assert self.config is not None
        uvicorn.run(app, host=host, port=port or self.config.api_port)
