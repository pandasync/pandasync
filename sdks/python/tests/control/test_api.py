"""Tests for the REST API."""

from pandasync._version import __version__


class TestRoot:
    def test_root_returns_info(self, api_client):
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "PandaSync"
        assert data["version"] == __version__


class TestDevices:
    def test_list_devices_returns_self(self, api_client):
        response = api_client.get("/api/v1/devices")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "TestDevice"
        assert data[0]["channels_in"] == 2
        assert data[0]["channels_out"] == 2


class TestSources:
    def test_list_sources(self, api_client):
        response = api_client.get("/api/v1/sources")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "TestDevice:out1"
        assert data[1]["name"] == "TestDevice:out2"
        assert data[0]["sample_rate"] == 48000


class TestReceivers:
    def test_list_receivers(self, api_client):
        response = api_client.get("/api/v1/receivers")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["name"] == "TestDevice:in1"
        assert data[1]["name"] == "TestDevice:in2"


class TestStatus:
    def test_get_status(self, api_client):
        response = api_client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == __version__
        assert data["clock_status"] == "free_run"
        assert data["clock_role"] == "listener"
        assert data["active_connections"] == 0
        assert "uptime_seconds" in data


class TestNoDevice:
    def test_503_without_device(self):
        """Routes return 503 when no device is configured."""
        from fastapi.testclient import TestClient

        from pandasync.control.api import create_app

        client = TestClient(create_app())
        response = client.get("/api/v1/devices")
        assert response.status_code == 503
