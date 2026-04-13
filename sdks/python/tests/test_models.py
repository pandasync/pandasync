"""Tests for core domain models."""

from pandasync.models import (
    AudioSource,
    ClockRole,
    ClockStatus,
    Connection,
    DeviceInfo,
    DeviceStatus,
    Receiver,
    TransportType,
)


class TestDeviceInfo:
    def test_default_values(self):
        device = DeviceInfo(name="TestDevice", host="192.168.1.10")
        assert device.name == "TestDevice"
        assert device.host == "192.168.1.10"
        assert device.port == 9820
        assert device.channels_in == 0
        assert device.channels_out == 0
        assert device.clock_status == ClockStatus.UNKNOWN
        assert device.profile == "simple"

    def test_custom_values(self):
        device = DeviceInfo(
            name="Mixer",
            host="10.0.0.5",
            port=8080,
            channels_in=32,
            channels_out=32,
            clock_status=ClockStatus.LOCKED,
            clock_role=ClockRole.GRANDMASTER,
            profile="broadcast",
        )
        assert device.channels_in == 32
        assert device.clock_status == ClockStatus.LOCKED
        assert device.clock_role == ClockRole.GRANDMASTER

    def test_serialization_roundtrip(self):
        device = DeviceInfo(name="Test", host="127.0.0.1")
        data = device.model_dump()
        restored = DeviceInfo.model_validate(data)
        assert restored.name == device.name
        assert restored.id == device.id


class TestAudioSource:
    def test_defaults(self):
        from uuid import uuid4
        source = AudioSource(device_id=uuid4(), name="mic1", channels=2)
        assert source.sample_rate == 48000
        assert source.bit_depth == 24
        assert source.channels == 2


class TestReceiver:
    def test_defaults(self):
        from uuid import uuid4
        receiver = Receiver(device_id=uuid4(), name="input1", channels=4)
        assert receiver.sample_rate == 48000
        assert receiver.channels == 4


class TestConnection:
    def test_defaults(self):
        from uuid import uuid4
        conn = Connection(source_id=uuid4(), receiver_id=uuid4())
        assert conn.transport == TransportType.AUTO
        assert conn.active is True
        assert conn.latency_ms == 0.0


class TestDeviceStatus:
    def test_creation(self):
        device = DeviceInfo(name="Test", host="127.0.0.1")
        status = DeviceStatus(device=device)
        assert status.clock_status == ClockStatus.UNKNOWN
        assert status.active_connections == 0


class TestEnums:
    def test_transport_type_values(self):
        assert TransportType.AUTO.value == "auto"
        assert TransportType.RTP.value == "rtp"
        assert TransportType.QUIC.value == "quic"
        assert TransportType.WEBRTC.value == "webrtc"

    def test_clock_status_values(self):
        assert ClockStatus.LOCKED.value == "locked"
        assert ClockStatus.FREE_RUN.value == "free_run"
