"""Clock manager -- auto-configures the PTP clock hierarchy.

Handles grandmaster election, boundary clock assignment, health
monitoring, and automatic failover.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from pandasync.clock.ptp import PTPClock
from pandasync.models import ClockRole, ClockStatus, DeviceInfo

logger = logging.getLogger(__name__)


@dataclass
class ClockManager:
    """Manages clock synchronization for a PandaSync device."""

    local_clock: PTPClock = field(default_factory=PTPClock)
    _devices: list[DeviceInfo] = field(default_factory=list)

    def auto_configure(self, devices: list[DeviceInfo]) -> None:
        """Auto-configure the clock hierarchy from discovered devices.

        1. If an external grandmaster is detected, sync to it.
        2. Otherwise, elect the best device as grandmaster.
        3. Assign boundary and slave roles.
        4. Start health monitoring.
        """
        self._devices = devices

        if self._detect_external_grandmaster():
            logger.info("External grandmaster detected, syncing")
            self.local_clock.status = ClockStatus.LOCKING
            return

        if not devices:
            logger.info("No other devices found, running as grandmaster")
            self.local_clock.role = ClockRole.GRANDMASTER
            self.local_clock.status = ClockStatus.LOCKED
            return

        gm = self._elect_grandmaster(devices)
        if gm and gm.name == self.local_clock.grandmaster_id:
            self.local_clock.role = ClockRole.GRANDMASTER
            self.local_clock.status = ClockStatus.LOCKED
        else:
            self.local_clock.role = ClockRole.SLAVE
            self.local_clock.status = ClockStatus.LOCKING

        logger.info(
            "Clock configured: role=%s, status=%s",
            self.local_clock.role.value,
            self.local_clock.status.value,
        )

    def get_status(self) -> PTPClock:
        """Return the current clock state."""
        return self.local_clock

    def _detect_external_grandmaster(self) -> bool:
        """Check if an external PTP grandmaster is available on the network."""
        # TODO: Query system PTP daemon for external GM
        return False

    def _elect_grandmaster(self, devices: list[DeviceInfo]) -> DeviceInfo | None:
        """Elect the best device as grandmaster based on capability."""
        if not devices:
            return None
        # Simple election: first device alphabetically (placeholder)
        return sorted(devices, key=lambda d: d.name)[0]
