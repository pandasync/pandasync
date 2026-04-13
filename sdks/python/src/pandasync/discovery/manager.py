"""Discovery manager -- orchestrates all three discovery tiers.

Scans configured tiers, deduplicates results, and provides a unified
view of all discovered devices.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pandasync.discovery.mdns import MDNSDiscovery
from pandasync.models import DeviceInfo  # noqa: TC001 - required at runtime

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryManager:
    """Manages device discovery across all configured tiers."""

    tiers: list[str] = field(default_factory=lambda: ["mdns"])
    _mdns: MDNSDiscovery = field(default_factory=MDNSDiscovery)

    def start(self) -> None:
        """Start discovery on all configured tiers."""
        if "mdns" in self.tiers:
            self._mdns.start()
            logger.info("Tier 1 (mDNS) discovery started")

        if "dns_sd" in self.tiers:
            logger.warning("Tier 2 (unicast DNS-SD) is not yet implemented")

        if "cloud" in self.tiers:
            logger.warning("Tier 3 (cloud registry) is not yet implemented")

    def stop(self) -> None:
        """Stop all discovery tiers."""
        self._mdns.stop()

    def discover(self) -> list[DeviceInfo]:
        """Scan all configured tiers and return deduplicated devices."""
        devices: list[DeviceInfo] = []

        if "mdns" in self.tiers:
            devices.extend(self._mdns.get_devices())

        # Future: add dns_sd and cloud results

        return self._deduplicate(devices)

    def register(self, device: DeviceInfo) -> None:
        """Register a device on all configured tiers."""
        if "mdns" in self.tiers:
            self._mdns.register(device)

    def unregister(self, device: DeviceInfo) -> None:
        """Unregister a device from all tiers."""
        if "mdns" in self.tiers:
            self._mdns.unregister(device)

    def _deduplicate(self, devices: list[DeviceInfo]) -> list[DeviceInfo]:
        """Remove duplicate devices discovered across multiple tiers."""
        seen: dict[str, DeviceInfo] = {}
        for device in devices:
            key = f"{device.host}:{device.port}"
            if key not in seen:
                seen[key] = device
        return list(seen.values())
