"""GET /api/v1/sources -- list available audio sources."""

from fastapi import APIRouter

from pandasync.models import AudioSource

router = APIRouter()


@router.get("/sources", response_model=list[AudioSource])
async def list_sources() -> list[AudioSource]:
    """List all available audio sources across discovered devices."""
    # TODO: Wire to Device.sources
    return []
