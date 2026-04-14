"""Tests for the streams API routes."""

import pytest
from fastapi.testclient import TestClient

from pandasync.control.api import create_app
from pandasync.device import Device


@pytest.fixture
def streams_device() -> Device:
    """Device with a streams manager using an isolated port range."""
    device = Device(name="StreamsTest", channels_in=2, channels_out=2)
    device._streams.base_port = 18000
    yield device
    device._streams.stop_all()


@pytest.fixture
def streams_client(streams_device: Device) -> TestClient:
    app = create_app(device=streams_device)
    return TestClient(app)


class TestStreamsReceive:
    def test_prepare_receive_returns_port(self, streams_client):
        response = streams_client.post(
            "/api/v1/streams/receive",
            json={"source": "Src:out1", "destination": "Dst:in1"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "stream_id" in data
        assert data["port"] == 18000


class TestStreamsList:
    def test_empty_streams(self, streams_client):
        response = streams_client.get("/api/v1/streams")
        assert response.status_code == 200
        assert response.json() == []

    def test_stream_appears_after_receive(self, streams_client):
        streams_client.post(
            "/api/v1/streams/receive",
            json={"source": "A:o1", "destination": "B:i1"},
        )
        response = streams_client.get("/api/v1/streams")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["role"] == "receiver"


class TestStreamsStop:
    def test_stop_existing_stream(self, streams_client):
        create = streams_client.post(
            "/api/v1/streams/receive",
            json={"source": "A:o1", "destination": "B:i1"},
        )
        stream_id = create.json()["stream_id"]

        stop = streams_client.post(
            "/api/v1/streams/stop",
            json={"stream_id": stream_id},
        )
        assert stop.status_code == 200
        assert stop.json()["stopped"] is True

    def test_stop_unknown_stream(self, streams_client):
        import uuid

        response = streams_client.post(
            "/api/v1/streams/stop",
            json={"stream_id": str(uuid.uuid4())},
        )
        assert response.status_code == 200
        assert response.json()["stopped"] is False
