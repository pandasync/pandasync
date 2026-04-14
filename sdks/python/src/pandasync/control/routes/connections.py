"""POST /api/v1/connect and /api/v1/disconnect -- manage audio connections."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from pandasync.control.dependencies import get_device
from pandasync.control.models import (
    ConnectRequest,
    ConnectResponse,
    DisconnectRequest,
    DisconnectResponse,
)
from pandasync.device import Device

router = APIRouter()


@router.post("/connect", response_model=ConnectResponse)
async def create_connection(
    request: ConnectRequest,
    device: Device = Depends(get_device),
) -> ConnectResponse:
    """Create an audio connection between a source and a receiver."""
    connection = device.connect(
        request.source,
        request.destination,
        request.transport,
        verification=request.verification,
        drop_rate=request.drop_rate,
    )
    return ConnectResponse(
        connection_id=connection.id,
        source=request.source,
        destination=request.destination,
        transport=connection.transport,
    )


@router.post("/disconnect", response_model=DisconnectResponse)
async def remove_connection(
    request: DisconnectRequest,
    device: Device = Depends(get_device),
) -> DisconnectResponse:
    """Disconnect an active audio connection."""
    device.disconnect(request.connection_id)
    return DisconnectResponse(connection_id=request.connection_id)
