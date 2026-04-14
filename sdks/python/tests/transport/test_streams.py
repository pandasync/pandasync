"""Tests for the StreamManager."""

import time

from pandasync.transport.streams import StreamManager


class TestStreamManager:
    def test_create_receiver_returns_id_and_port(self):
        mgr = StreamManager(base_port=17000)
        stream_id, port = mgr.create_receiver("Test:out1->Local:in1")
        try:
            assert port == 17000
            assert stream_id is not None
        finally:
            mgr.stop_all()

    def test_port_allocation_is_even(self):
        mgr = StreamManager(base_port=17010)
        ids_and_ports = [mgr.create_receiver(f"s{i}") for i in range(3)]
        try:
            ports = [p for _, p in ids_and_ports]
            assert ports == [17010, 17012, 17014]
        finally:
            mgr.stop_all()

    def test_stop_stream_removes_it(self):
        mgr = StreamManager(base_port=17020)
        stream_id, _ = mgr.create_receiver("Test")
        try:
            assert mgr.stop_stream(stream_id) is True
            assert mgr.stop_stream(stream_id) is False
        finally:
            mgr.stop_all()

    def test_stats_includes_active_streams(self):
        mgr = StreamManager(base_port=17030)
        stream_id, _ = mgr.create_receiver("Foo:out1->Bar:in1")
        try:
            stats = mgr.get_stats()
            assert len(stats) == 1
            assert stats[0]["role"] == "receiver"
            assert stats[0]["source_desc"] == "Foo:out1->Bar:in1"
            assert str(stream_id) == stats[0]["stream_id"]
        finally:
            mgr.stop_all()

    def test_sender_and_receiver_together(self):
        """Full local loopback: manager creates a receiver, then a sender
        targeting it, and packets flow."""
        mgr = StreamManager(base_port=17040)
        recv_id, port = mgr.create_receiver("Test")
        try:
            send_id = mgr.create_sender(
                source_desc="Test:out1->Test:in1",
                dest_host="127.0.0.1",
                dest_port=port,
            )
            try:
                time.sleep(0.3)
                stats = mgr.get_stats()
                assert len(stats) == 2

                by_role = {s["role"]: s for s in stats}
                assert by_role["sender"]["packets_sent"] > 0
                assert by_role["receiver"]["packets_received"] > 0
            finally:
                mgr.stop_stream(send_id)
        finally:
            mgr.stop_stream(recv_id)

    def test_stop_all(self):
        mgr = StreamManager(base_port=17060)
        mgr.create_receiver("a")
        mgr.create_receiver("b")
        assert len(mgr.get_stats()) == 2
        mgr.stop_all()
        assert len(mgr.get_stats()) == 0
