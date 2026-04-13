"""PandaSync device -- the central integration class.

Wires together all five layers: transport, clock, discovery,
control plane, and applications. This is the main entry point
for embedding PandaSync in a product or application.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from pandasync._version import __version__
from pandasync.clock.manager import ClockManager
from pandasync.config import Config
from pandasync.discovery.manager import DiscoveryManager
from pandasync.models import (
    AudioSource,
    Connection,
    DeviceInfo,
    Receiver,
    TransportType,
)
from pandasync.profiles import Profile

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
    _connections: list[Connection] = field(default_factory=list, repr=False)
    _running: bool = field(default=False, repr=False)

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

        self._running = True
        logger.info("Device '%s' started (profile=%s)", self.name, self.profile.value)

    def stop(self) -> None:
        """Stop the device and clean up resources."""
        if not self._running:
            return

        if self._discovery:
            self._discovery.unregister(self.info)
            self._discovery.stop()

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
    ) -> Connection:
        """Create an audio connection between a source and a receiver.

        Args:
            source: Source identifier (e.g., "MicArray:ch1-8").
            destination: Receiver identifier (e.g., "Recorder:ch1-8").
            transport: Transport type to use (default: auto-select).

        Returns:
            The created Connection object.
        """
        connection = Connection(
            source_id=uuid4(),  # TODO: resolve from source string
            receiver_id=uuid4(),  # TODO: resolve from destination string
            transport=transport,
        )
        self._connections.append(connection)
        logger.info(
            "Connection created: %s -> %s via %s",
            source,
            destination,
            transport.value,
        )
        return connection

    def disconnect(self, connection_id: UUID) -> None:
        """Disconnect an active audio connection."""
        self._connections = [c for c in self._connections if c.id != connection_id]
        logger.info("Connection %s disconnected", connection_id)

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
