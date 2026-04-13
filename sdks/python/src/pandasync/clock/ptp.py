"""IEEE 1588v2 PTP clock management.

This is a management layer that wraps system PTP daemons (e.g., linuxptp).
Pure-Python PTP cannot achieve the sub-microsecond timing required for
production use. The C SDK will contain the native PTP stack.
"""

from __future__ import annotations

from dataclasses import dataclass

from pandasync.models import ClockRole, ClockStatus


@dataclass
class PTPClock:
    """Represents this device's PTP clock state."""

    status: ClockStatus = ClockStatus.FREE_RUN
    role: ClockRole = ClockRole.LISTENER
    offset_from_master_us: float = 0.0
    grandmaster_id: str = ""

    def is_synchronized(self) -> bool:
        """Check if the clock is locked to a grandmaster."""
        return self.status == ClockStatus.LOCKED
