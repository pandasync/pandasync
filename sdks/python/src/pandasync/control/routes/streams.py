"""RTP stream management routes.

POST /api/v1/streams/receive -- prepare a receiver
POST /api/v1/streams/stop    -- stop a stream
GET  /api/v1/streams         -- list active streams with stats
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from pandasync.control.dependencies import get_device
from pandasync.control.models import (
    StreamReceiveRequest,
    StreamReceiveResponse,
    StreamStopRequest,
    StreamStopResponse,
)
from pandasync.device import Device

router = APIRouter()


@router.post("/streams/receive", response_model=StreamReceiveResponse)
async def prepare_receive(
    request: StreamReceiveRequest,
    device: Device = Depends(get_device),
) -> StreamReceiveResponse:
    """Prepare an RTP receiver for an incoming stream.

    Returns the stream_id and port the caller should send RTP packets to.
    """
    stream_id, port = device.prepare_receive(
        source=request.source,
        destination=request.destination,
        verification=request.verification,
    )
    return StreamReceiveResponse(stream_id=stream_id, port=port)


@router.post("/streams/stop", response_model=StreamStopResponse)
async def stop_stream(
    request: StreamStopRequest,
    device: Device = Depends(get_device),
) -> StreamStopResponse:
    """Stop an RTP stream (sender or receiver) by ID."""
    stopped = device.stop_stream(request.stream_id)
    return StreamStopResponse(
        stream_id=request.stream_id,
        stopped=stopped,
    )


@router.get("/streams")
async def list_streams(
    device: Device = Depends(get_device),
) -> list[dict[str, Any]]:
    """List all active RTP streams with per-stream statistics."""
    return device.streams.get_stats()
