"""QUIC transport for WAN and lossy networks.

Provides stream multiplexing, built-in FEC hooks, and NAT traversal.
Not yet implemented.
"""

from pandasync.exceptions import NotImplementedYetError

TRACKING_URL = "https://github.com/pandasync/pandasync/issues"


def create_quic_transport() -> None:
    """Create a QUIC transport instance."""
    raise NotImplementedYetError("QUIC transport", TRACKING_URL)
