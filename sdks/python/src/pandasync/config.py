"""Configuration for PandaSync devices."""

from __future__ import annotations

from dataclasses import dataclass, field

from pandasync.profiles import Profile


@dataclass
class Config:
    """PandaSync device configuration.

    Defaults vary by profile. Use `Config.for_profile()` to get
    profile-appropriate defaults.
    """

    device_name: str = "PandaSync Device"
    channels_in: int = 2
    channels_out: int = 2
    profile: Profile = Profile.SIMPLE
    api_port: int = 9820
    sample_rate: int = 48000
    bit_depth: int = 24

    # Discovery
    mdns_enabled: bool = True
    dns_sd_enabled: bool = False
    cloud_registry_enabled: bool = False

    # Clock
    clock_source: str = "auto"
    latency_ms: float = 2.0

    # Control
    metrics_enabled: bool = False
    websocket_throttled: bool = True

    # Network
    multicast_ttl: int = 1

    # Auth
    auth_mode: str = "bearer_optional"

    discovery_tiers: list[str] = field(default_factory=lambda: ["mdns"])

    @classmethod
    def for_profile(cls, profile: Profile, **overrides: object) -> Config:
        """Create a configuration with profile-appropriate defaults."""
        defaults: dict[str, object]

        if profile == Profile.SIMPLE:
            defaults = {
                "profile": Profile.SIMPLE,
                "latency_ms": 2.0,
                "clock_source": "auto",
                "mdns_enabled": True,
                "dns_sd_enabled": False,
                "cloud_registry_enabled": False,
                "metrics_enabled": False,
                "websocket_throttled": True,
                "multicast_ttl": 1,
                "auth_mode": "bearer_optional",
                "discovery_tiers": ["mdns"],
            }
        elif profile == Profile.BROADCAST:
            defaults = {
                "profile": Profile.BROADCAST,
                "latency_ms": 1.0,
                "clock_source": "external_gm",
                "mdns_enabled": True,
                "dns_sd_enabled": True,
                "cloud_registry_enabled": True,
                "metrics_enabled": True,
                "websocket_throttled": False,
                "multicast_ttl": 32,
                "auth_mode": "mtls_required",
                "discovery_tiers": ["mdns", "dns_sd", "cloud"],
            }
        else:  # DEVELOPER
            defaults = {
                "profile": Profile.DEVELOPER,
                "latency_ms": 1.0,
                "clock_source": "auto",
                "mdns_enabled": True,
                "dns_sd_enabled": True,
                "cloud_registry_enabled": True,
                "metrics_enabled": True,
                "websocket_throttled": False,
                "multicast_ttl": 32,
                "auth_mode": "bearer_or_mtls",
                "discovery_tiers": ["mdns", "dns_sd", "cloud"],
            }

        defaults.update(overrides)
        return cls(**defaults)  # type: ignore[arg-type]
