"""GET /api/v1/receivers -- list available audio receivers."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from pandasync.control.dependencies import get_device
from pandasync.device import Device
from pandasync.models import Receiver

router = APIRouter()


@router.get("/receivers", response_model=list[Receiver])
async def list_receivers(
    device: Device = Depends(get_device),
) -> list[Receiver]:
    """List all available audio receivers on this device."""
    return device.receivers
