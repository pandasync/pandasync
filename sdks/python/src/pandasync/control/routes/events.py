"""WS /api/v1/events -- real-time status WebSocket."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


@router.websocket("/events")
async def event_stream(websocket: WebSocket) -> None:
    """Real-time event stream via WebSocket.

    Clients receive JSON messages for device state changes,
    connection updates, and clock status changes.
    """
    await websocket.accept()
    try:
        # TODO: Wire to event bus
        await websocket.send_json({
            "type": "connected",
            "message": "PandaSync event stream active",
        })
        while True:
            # Keep connection alive, wait for client messages
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "echo",
                "data": data,
            })
    except WebSocketDisconnect:
        pass
