"""Tests for configuration and profiles."""

from pandasync.config import Config
from pandasync.profiles import Profile


class TestConfig:
    def test_default_config(self):
        config = Config()
        assert config.profile == Profile.SIMPLE
        assert config.api_port == 9820
        assert config.sample_rate == 48000

    def test_simple_profile_defaults(self):
        config = Config.for_profile(Profile.SIMPLE)
        assert config.latency_ms == 2.0
        assert config.clock_source == "auto"
        assert config.mdns_enabled is True
        assert config.dns_sd_enabled is False
        assert config.cloud_registry_enabled is False
        assert config.metrics_enabled is False
        assert config.websocket_throttled is True
        assert config.multicast_ttl == 1
        assert config.auth_mode == "bearer_optional"
        assert config.discovery_tiers == ["mdns"]

    def test_broadcast_profile_defaults(self):
        config = Config.for_profile(Profile.BROADCAST)
        assert config.latency_ms == 1.0
        assert config.clock_source == "external_gm"
        assert config.dns_sd_enabled is True
        assert config.cloud_registry_enabled is True
        assert config.metrics_enabled is True
        assert config.websocket_throttled is False
        assert config.multicast_ttl == 32
        assert config.auth_mode == "mtls_required"
        assert config.discovery_tiers == ["mdns", "dns_sd", "cloud"]

    def test_developer_profile_defaults(self):
        config = Config.for_profile(Profile.DEVELOPER)
        assert config.latency_ms == 1.0
        assert config.clock_source == "auto"
        assert config.dns_sd_enabled is True
        assert config.metrics_enabled is True
        assert config.websocket_throttled is False
        assert config.auth_mode == "bearer_or_mtls"
        assert config.discovery_tiers == ["mdns", "dns_sd", "cloud"]

    def test_profile_with_overrides(self):
        config = Config.for_profile(
            Profile.SIMPLE,
            device_name="CustomMixer",
            channels_in=16,
        )
        assert config.device_name == "CustomMixer"
        assert config.channels_in == 16
        assert config.latency_ms == 2.0  # still gets simple defaults


class TestProfile:
    def test_profile_values(self):
        assert Profile.SIMPLE.value == "simple"
        assert Profile.BROADCAST.value == "broadcast"
        assert Profile.DEVELOPER.value == "developer"

    def test_profile_from_string(self):
        assert Profile("simple") == Profile.SIMPLE
        assert Profile("broadcast") == Profile.BROADCAST
        assert Profile("developer") == Profile.DEVELOPER
