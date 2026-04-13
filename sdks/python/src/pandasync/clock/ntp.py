"""NTP fallback for WAN and cloud endpoints where PTP is not available.

Not yet implemented.
"""

from pandasync.exceptions import NotImplementedYetError

TRACKING_URL = "https://github.com/pandasync/pandasync/issues"


def create_ntp_clock() -> None:
    """Create an NTP-based clock source."""
    raise NotImplementedYetError("NTP clock fallback", TRACKING_URL)
