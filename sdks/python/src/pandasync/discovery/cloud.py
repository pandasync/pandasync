"""Tier 3 -- Cloud registry for WAN and multi-site discovery.

Optional. Devices register with a global service for WAN and hybrid
production workflows. Not yet implemented.
"""

from pandasync.exceptions import NotImplementedYetError

TRACKING_URL = "https://github.com/pandasync/pandasync/issues"


def create_cloud_discovery() -> None:
    """Create a cloud registry discovery instance."""
    raise NotImplementedYetError("Cloud registry discovery", TRACKING_URL)
