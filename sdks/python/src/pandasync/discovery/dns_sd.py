"""Tier 2 -- Unicast DNS-SD discovery for cross-subnet / facility use.

Devices register with a local DNS server. Works across VLANs and subnets.
Not yet implemented.
"""

from pandasync.exceptions import NotImplementedYetError

TRACKING_URL = "https://github.com/pandasync/pandasync/issues"


def create_dns_sd_discovery() -> None:
    """Create a unicast DNS-SD discovery instance."""
    raise NotImplementedYetError("Unicast DNS-SD discovery", TRACKING_URL)
