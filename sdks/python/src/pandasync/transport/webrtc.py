"""WebRTC transport for browser-based monitoring and cloud bridges.

Not yet implemented.
"""

from pandasync.exceptions import NotImplementedYetError

TRACKING_URL = "https://github.com/pandasync/pandasync/issues"


def create_webrtc_transport() -> None:
    """Create a WebRTC transport instance."""
    raise NotImplementedYetError("WebRTC transport", TRACKING_URL)
