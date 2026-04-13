"""GET /api/v1/status -- device and clock status."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from pandasync._version import __version__
from pandasync.control.dependencies import get_device
from pandasync.control.models import StatusResponse
from pandasync.device import Device

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status(
    device: Device = Depends(get_device),
) -> StatusResponse:
    """Return the current status of this PandaSync device."""
    clock = device._clock
    return StatusResponse(
        version=__version__,
        clock_status=clock.local_clock.status.value if clock else "free_run",
        clock_role=clock.local_clock.role.value if clock else "listener",
        clock_offset_us=(clock.local_clock.offset_from_master_us if clock else 0.0),
        active_connections=len(device.connections),
        uptime_seconds=device.uptime_seconds,
    )
