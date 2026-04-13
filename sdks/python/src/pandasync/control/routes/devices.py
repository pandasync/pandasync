"""GET /api/v1/devices -- list all discovered devices."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from pandasync.control.dependencies import get_device
from pandasync.device import Device
from pandasync.models import DeviceInfo

router = APIRouter()


@router.get("/devices", response_model=list[DeviceInfo])
async def list_devices(
    device: Device = Depends(get_device),
) -> list[DeviceInfo]:
    """List all PandaSync devices: this device plus discovered peers."""
    return [device.info, *device.discover()]
