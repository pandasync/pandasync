"""PandaSync exception hierarchy."""


class PandaSyncError(Exception):
    """Base exception for all PandaSync errors."""


class DiscoveryError(PandaSyncError):
    """Raised when device discovery fails."""


class ConnectionError(PandaSyncError):
    """Raised when an audio connection cannot be established."""


class ClockError(PandaSyncError):
    """Raised when clock synchronization fails."""


class TransportError(PandaSyncError):
    """Raised when a transport-level error occurs."""


class NotImplementedYetError(PandaSyncError):
    """Raised when a feature is stubbed but not yet implemented."""

    def __init__(self, feature: str, tracking_url: str = "") -> None:
        msg = f"{feature} is not yet implemented."
        if tracking_url:
            msg += f" Track progress at: {tracking_url}"
        super().__init__(msg)
