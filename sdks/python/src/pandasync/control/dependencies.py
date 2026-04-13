"""FastAPI dependencies for the PandaSync control plane."""

from __future__ import annotations

from fastapi import HTTPException, Request


def get_device(request: Request) -> object:
    """Extract the Device instance from the FastAPI app state.

    Raises HTTP 503 if no device is configured.
    """
    device = getattr(request.app.state, "device", None)
    if device is None:
        raise HTTPException(
            status_code=503,
            detail="No device configured",
        )
    return device
