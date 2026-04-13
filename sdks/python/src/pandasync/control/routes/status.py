"""GET /api/v1/status -- device and clock status."""

from fastapi import APIRouter

from pandasync._version import __version__
from pandasync.control.models import StatusResponse

router = APIRouter()


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """Return the current status of this PandaSync device."""
    # TODO: Wire to Device and ClockManager
    return StatusResponse(
        version=__version__,
        clock_status="free_run",
        clock_role="listener",
        clock_offset_us=0.0,
        active_connections=0,
        uptime_seconds=0.0,
    )
