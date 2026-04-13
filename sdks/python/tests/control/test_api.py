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
    def test_list_devices_empty(self, api_client):
        response = api_client.get("/api/v1/devices")
        assert response.status_code == 200
        assert response.json() == []


class TestSources:
    def test_list_sources_empty(self, api_client):
        response = api_client.get("/api/v1/sources")
        assert response.status_code == 200
        assert response.json() == []


class TestReceivers:
    def test_list_receivers_empty(self, api_client):
        response = api_client.get("/api/v1/receivers")
        assert response.status_code == 200
        assert response.json() == []


class TestConnections:
    def test_connect(self, api_client):
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

    def test_disconnect(self, api_client):
        import uuid
        conn_id = str(uuid.uuid4())
        response = api_client.post(
            "/api/v1/disconnect",
            json={"connection_id": conn_id},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "disconnected"


class TestStatus:
    def test_get_status(self, api_client):
        response = api_client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == __version__
        assert data["clock_status"] == "free_run"
        assert "active_connections" in data
