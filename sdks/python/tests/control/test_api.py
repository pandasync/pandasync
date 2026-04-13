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


class TestConnections:
    def test_connect(self, api_client, device):
        response = api_client.post(
            "/api/v1/connect",
            json={
                "source": "MicArray:ch1",
                "destination": "Recorder:ch1",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "MicArray:ch1"
        assert data["destination"] == "Recorder:ch1"
        assert data["status"] == "connected"
        assert "connection_id" in data

        # Verify the connection exists on the device
        assert len(device.connections) == 1

    def test_connect_with_transport(self, api_client):
        response = api_client.post(
            "/api/v1/connect",
            json={
                "source": "Mixer:out1",
                "destination": "Speaker:in1",
                "transport": "rtp",
            },
        )
        assert response.status_code == 200
        assert response.json()["transport"] == "rtp"

    def test_disconnect(self, api_client, device):
        # First create a connection
        connect_resp = api_client.post(
            "/api/v1/connect",
            json={
                "source": "Mic:ch1",
                "destination": "Rec:ch1",
            },
        )
        conn_id = connect_resp.json()["connection_id"]
        assert len(device.connections) == 1

        # Then disconnect
        response = api_client.post(
            "/api/v1/disconnect",
            json={"connection_id": conn_id},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "disconnected"
        assert len(device.connections) == 0


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
