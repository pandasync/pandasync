"""POST /api/v1/connect and /api/v1/disconnect -- manage audio connections."""

from uuid import uuid4

from fastapi import APIRouter

from pandasync.control.models import (
    ConnectRequest,
    ConnectResponse,
    DisconnectRequest,
    DisconnectResponse,
)

router = APIRouter()


@router.post("/connect", response_model=ConnectResponse)
async def create_connection(request: ConnectRequest) -> ConnectResponse:
    """Create an audio connection between a source and a receiver."""
    # TODO: Wire to Device.connect
    return ConnectResponse(
        connection_id=uuid4(),
        source=request.source,
        destination=request.destination,
        transport=request.transport,
    )


@router.post("/disconnect", response_model=DisconnectResponse)
async def remove_connection(request: DisconnectRequest) -> DisconnectResponse:
    """Disconnect an active audio connection."""
    # TODO: Wire to Device.disconnect
    return DisconnectResponse(connection_id=request.connection_id)
