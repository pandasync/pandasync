"""Tier 1 -- mDNS/DNS-SD discovery using zeroconf.

Zero-config LAN discovery. Devices register and discover each other
via the `_pandasync._udp` service type.
"""

from __future__ import annotations

import logging
import socket

from zeroconf import ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf

from pandasync.models import DeviceInfo

logger = logging.getLogger(__name__)

SERVICE_TYPE = "_pandasync._udp.local."


class MDNSDiscovery:
    """mDNS/DNS-SD device discovery (Tier 1)."""

    def __init__(self) -> None:
        self._zeroconf: Zeroconf | None = None
        self._browser: ServiceBrowser | None = None
        self._devices: dict[str, DeviceInfo] = {}

    def start(self) -> None:
        """Start mDNS discovery."""
        self._zeroconf = Zeroconf()
        self._browser = ServiceBrowser(
            self._zeroconf,
            SERVICE_TYPE,
            handlers=[self._on_state_change],
        )
        logger.info("mDNS discovery started for %s", SERVICE_TYPE)

    def stop(self) -> None:
        """Stop mDNS discovery."""
        if self._zeroconf:
            self._zeroconf.close()
            self._zeroconf = None
        self._browser = None
        logger.info("mDNS discovery stopped")

    def get_devices(self) -> list[DeviceInfo]:
        """Return all currently discovered devices."""
        return list(self._devices.values())

    def register(self, device: DeviceInfo) -> None:
        """Register this device on the network via mDNS."""
        if not self._zeroconf:
            self.start()

        assert self._zeroconf is not None

        # Resolve this host's addresses for mDNS registration
        hostname = socket.gethostname()
        addresses = []
        try:
            for addr_info in socket.getaddrinfo(hostname, None, socket.AF_INET):
                addr = socket.inet_aton(str(addr_info[4][0]))
                if addr not in addresses:
                    addresses.append(addr)
        except OSError:
            pass

        info = ServiceInfo(
            SERVICE_TYPE,
            f"{device.name}.{SERVICE_TYPE}",
            port=device.port,
            addresses=addresses or None,
            server=f"{hostname}.local.",
            properties={
                "version": device.version,
                "channels_in": str(device.channels_in),
                "channels_out": str(device.channels_out),
                "profile": device.profile,
            },
        )
        self._zeroconf.register_service(info, allow_name_change=True)
        logger.info("Registered device '%s' via mDNS", device.name)

    def unregister(self, device: DeviceInfo) -> None:
        """Unregister this device from mDNS."""
        if not self._zeroconf:
            return

        info = ServiceInfo(
            SERVICE_TYPE,
            f"{device.name}.{SERVICE_TYPE}",
            port=device.port,
        )
        self._zeroconf.unregister_service(info)

    def _on_state_change(self, **kwargs: object) -> None:
        """Handle service state changes from the ServiceBrowser."""
        zeroconf: Zeroconf = kwargs["zeroconf"]  # type: ignore[assignment]
        service_type: str = kwargs["service_type"]  # type: ignore[assignment]
        name: str = kwargs["name"]  # type: ignore[assignment]
        state_change: ServiceStateChange = kwargs["state_change"]  # type: ignore[assignment]

        if state_change is ServiceStateChange.Added:
            self._on_service_added(zeroconf, service_type, name)
        elif state_change is ServiceStateChange.Removed:
            self._devices.pop(name, None)
            logger.info("Device removed: %s", name)
        elif state_change is ServiceStateChange.Updated:
            self._on_service_added(zeroconf, service_type, name)

    def _on_service_added(
        self, zeroconf: Zeroconf, service_type: str, name: str
    ) -> None:
        """Handle a newly discovered or updated service."""
        info = zeroconf.get_service_info(service_type, name, timeout=3000)
        if info:
            device = self._service_info_to_device(info, name)
            self._devices[name] = device
            logger.info("Discovered device: %s", device.name)

    def _service_info_to_device(self, info: ServiceInfo, name: str) -> DeviceInfo:
        """Convert a zeroconf ServiceInfo to a DeviceInfo."""
        props = info.properties or {}
        addresses = info.parsed_addresses()
        host = addresses[0] if addresses else "unknown"

        channels_in = props.get(b"channels_in", b"0") or b"0"
        channels_out = props.get(b"channels_out", b"0") or b"0"
        profile = (props.get(b"profile", b"simple") or b"simple").decode()
        version = (props.get(b"version", b"") or b"").decode()

        return DeviceInfo(
            name=name.replace(f".{SERVICE_TYPE}", ""),
            host=host,
            port=info.port or 9820,
            channels_in=int(channels_in),
            channels_out=int(channels_out),
            profile=profile,
            version=version,
        )
