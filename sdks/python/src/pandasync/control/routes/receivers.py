"""GET /api/v1/receivers -- list available audio receivers."""

from fastapi import APIRouter

from pandasync.models import Receiver

router = APIRouter()


@router.get("/receivers", response_model=list[Receiver])
async def list_receivers() -> list[Receiver]:
    """List all available audio receivers across discovered devices."""
    # TODO: Wire to Device.receivers
    return []
