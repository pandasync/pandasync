"""GET /api/v1/sources -- list available audio sources."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from pandasync.control.dependencies import get_device
from pandasync.device import Device
from pandasync.models import AudioSource

router = APIRouter()


@router.get("/sources", response_model=list[AudioSource])
async def list_sources(
    device: Device = Depends(get_device),
) -> list[AudioSource]:
    """List all available audio sources on this device."""
    return device.sources
