"""Tests for the discovery manager."""

from pandasync.discovery.manager import DiscoveryManager
from pandasync.models import DeviceInfo


class TestDiscoveryManager:
    def test_default_tiers(self):
        manager = DiscoveryManager()
        assert manager.tiers == ["mdns"]

    def test_custom_tiers(self):
        manager = DiscoveryManager(tiers=["mdns", "dns_sd"])
        assert "dns_sd" in manager.tiers

    def test_deduplicate(self):
        manager = DiscoveryManager()
        devices = [
            DeviceInfo(name="Device1", host="192.168.1.1", port=9820),
            DeviceInfo(name="Device1-copy", host="192.168.1.1", port=9820),
            DeviceInfo(name="Device2", host="192.168.1.2", port=9820),
        ]
        result = manager._deduplicate(devices)
        assert len(result) == 2
        hosts = {d.host for d in result}
        assert "192.168.1.1" in hosts
        assert "192.168.1.2" in hosts

    def test_deduplicate_different_ports(self):
        manager = DiscoveryManager()
        devices = [
            DeviceInfo(name="Device1", host="192.168.1.1", port=9820),
            DeviceInfo(name="Device1b", host="192.168.1.1", port=9821),
        ]
        result = manager._deduplicate(devices)
        assert len(result) == 2

    def test_deduplicate_empty(self):
        manager = DiscoveryManager()
        result = manager._deduplicate([])
        assert result == []
