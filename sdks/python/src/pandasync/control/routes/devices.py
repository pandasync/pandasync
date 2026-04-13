"""GET /api/v1/devices -- list all discovered devices."""

from fastapi import APIRouter

from pandasync.models import DeviceInfo

router = APIRouter()


@router.get("/devices", response_model=list[DeviceInfo])
async def list_devices() -> list[DeviceInfo]:
    """List all discovered PandaSync devices on the network."""
    # TODO: Wire to DiscoveryManager
    return []
