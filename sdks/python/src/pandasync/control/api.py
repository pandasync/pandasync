"""FastAPI application factory for the PandaSync control plane."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import FastAPI

from pandasync._version import __version__
from pandasync.control.routes import (
    connections,
    devices,
    events,
    receivers,
    sources,
    status,
)

if TYPE_CHECKING:
    from pandasync.device import Device


def create_app(device: Device | None = None) -> FastAPI:
    """Create the PandaSync REST API application.

    Args:
        device: Optional Device instance to wire into the API routes.
            If None, routes that require a device will return HTTP 503.
    """
    app = FastAPI(
        title="PandaSync",
        description=(
            "PandaSync device control API."
            " Plug-in simplicity. Broadcast grade. Completely open."
        ),
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    app.state.device = device

    # Mount all v1 routes under /api/v1
    app.include_router(devices.router, prefix="/api/v1", tags=["devices"])
    app.include_router(sources.router, prefix="/api/v1", tags=["sources"])
    app.include_router(receivers.router, prefix="/api/v1", tags=["receivers"])
    app.include_router(connections.router, prefix="/api/v1", tags=["connections"])
    app.include_router(status.router, prefix="/api/v1", tags=["status"])
    app.include_router(events.router, prefix="/api/v1", tags=["events"])

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": "PandaSync",
            "version": __version__,
            "api": "/api/v1",
            "docs": "/api/docs",
        }

    return app
