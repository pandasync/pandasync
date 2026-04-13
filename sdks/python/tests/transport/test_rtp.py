"""Tests for the RTP transport."""

from pandasync.transport.rtp import RTPConfig, RTPSender


class TestRTPConfig:
    def test_defaults(self):
        config = RTPConfig()
        assert config.sample_rate == 48000
        assert config.channels == 2
        assert config.bit_depth == 24
        assert config.packet_time_ms == 1.0
        assert config.payload_type == 97


class TestRTPSender:
    def test_build_header(self):
        sender = RTPSender()
        sender._ssrc = 12345
        header = sender._build_header()
        assert len(header) == 12
        assert header[0] == 0x80  # V=2, P=0, X=0, CC=0

    def test_sequence_increments(self):
        sender = RTPSender()
        sender._ssrc = 1
        h1 = sender._build_header()
        sender._sequence = 1
        h2 = sender._build_header()
        # Sequence number is bytes 2-3
        assert h1[2:4] != h2[2:4]
