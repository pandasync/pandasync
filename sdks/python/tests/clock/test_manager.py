"""Tests for the clock manager."""

from pandasync.clock.manager import ClockManager
from pandasync.clock.ptp import PTPClock
from pandasync.models import ClockRole, ClockStatus, DeviceInfo


class TestPTPClock:
    def test_default_state(self):
        clock = PTPClock()
        assert clock.status == ClockStatus.FREE_RUN
        assert clock.role == ClockRole.LISTENER
        assert not clock.is_synchronized()

    def test_synchronized(self):
        clock = PTPClock(status=ClockStatus.LOCKED)
        assert clock.is_synchronized()


class TestClockManager:
    def test_auto_configure_no_devices(self):
        manager = ClockManager()
        manager.auto_configure([])
        assert manager.local_clock.role == ClockRole.GRANDMASTER
        assert manager.local_clock.status == ClockStatus.LOCKED

    def test_auto_configure_with_devices(self):
        manager = ClockManager()
        devices = [
            DeviceInfo(name="DeviceB", host="192.168.1.2"),
            DeviceInfo(name="DeviceA", host="192.168.1.1"),
        ]
        manager.auto_configure(devices)
        # Should elect a GM and set this device as slave
        assert manager.local_clock.role == ClockRole.SLAVE
        assert manager.local_clock.status == ClockStatus.LOCKING

    def test_get_status(self):
        manager = ClockManager()
        status = manager.get_status()
        assert isinstance(status, PTPClock)
