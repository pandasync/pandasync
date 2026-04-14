"""Tests for the RTP transport."""

import time

from pandasync.transport.rtp import (
    RTPConfig,
    RTPReceiver,
    RTPSender,
    _build_rtp_header,
    _generate_tone_samples,
)


class TestRTPConfig:
    def test_defaults(self):
        config = RTPConfig()
        assert config.sample_rate == 48000
        assert config.channels == 1
        assert config.bit_depth == 24
        assert config.packet_time_ms == 1.0
        assert config.payload_type == 97


class TestRTPHeader:
    def test_header_length(self):
        header = _build_rtp_header(0, 0, 0, 97)
        assert len(header) == 12

    def test_version_bits(self):
        header = _build_rtp_header(0, 0, 0, 97)
        assert header[0] == 0x80  # V=2

    def test_sequence_in_header(self):
        h1 = _build_rtp_header(1, 0, 0, 97)
        h2 = _build_rtp_header(2, 0, 0, 97)
        assert h1[2:4] != h2[2:4]


class TestToneGenerator:
    def test_generate_24bit(self):
        data, phase = _generate_tone_samples(48, 0.0, 440.0, 48000, 24)
        assert len(data) == 48 * 3  # 48 samples * 3 bytes
        assert 0 <= phase <= 2 * 3.14159 + 0.1

    def test_generate_16bit(self):
        data, phase = _generate_tone_samples(48, 0.0, 440.0, 48000, 16)
        assert len(data) == 48 * 2


class TestRTPSenderReceiver:
    """Integration test: sender and receiver in the same process."""

    def test_packets_flow_locally(self):
        # Use a unique port for this test
        port = 15004

        # Start receiver
        receiver = RTPReceiver(port=port)
        receiver.start()

        try:
            # Start sender targeting the receiver
            cfg = RTPConfig(packet_time_ms=1.0)
            sender = RTPSender(
                dest_host="127.0.0.1",
                dest_port=port,
                config=cfg,
            )
            sender.start()

            try:
                # Let packets flow for 100ms
                time.sleep(0.25)
            finally:
                sender.stop()

            # Give the receiver a moment to drain
            time.sleep(0.1)

            send_stats = sender.stats()
            recv_stats = receiver.stats()

            assert send_stats["packets_sent"] > 50
            assert recv_stats["packets_received"] > 10
            assert recv_stats["bytes_received"] > 0
        finally:
            receiver.stop()

    def test_sender_stats_before_start(self):
        sender = RTPSender(dest_host="127.0.0.1", dest_port=5004)
        stats = sender.stats()
        assert stats["packets_sent"] == 0
        assert stats["uptime_seconds"] == 0.0

    def test_receiver_stats_before_start(self):
        receiver = RTPReceiver(port=15005)
        stats = receiver.stats()
        assert stats["packets_received"] == 0
        assert stats["uptime_seconds"] == 0.0


class TestVerificationAndJitter:
    def test_verification_flow(self):
        port = 15100

        recv_cfg = RTPConfig(verification=True)
        receiver = RTPReceiver(port=port, config=recv_cfg)
        receiver.start()

        try:
            send_cfg = RTPConfig(verification=True, packet_time_ms=1.0)
            sender = RTPSender(
                dest_host="127.0.0.1",
                dest_port=port,
                config=send_cfg,
            )
            sender.start()

            try:
                time.sleep(0.3)
            finally:
                sender.stop()

            time.sleep(0.1)

            stats = receiver.stats()
            assert stats["packets_received"] > 50
            assert stats["verification_errors"] == 0
            jitter = stats["jitter"]
            assert jitter["samples"] > 10
            assert jitter["stddev_ms"] is not None
            assert stats["latency"]["mean_ns"] is not None
        finally:
            receiver.stop()

    def test_drop_rate(self):
        cfg = RTPConfig(drop_rate=0.5)
        sender = RTPSender(dest_host="127.0.0.1", dest_port=15101, config=cfg)
        sender.start()
        try:
            time.sleep(0.3)
        finally:
            sender.stop()

        stats = sender.stats()
        assert stats["packets_dropped"] > 50
        total = stats["packets_sent"] + stats["packets_dropped"]
        assert total > 250
