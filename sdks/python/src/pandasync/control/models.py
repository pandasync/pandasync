"""Pydantic models for the REST API request/response shapes."""

from __future__ import annotations

from uuid import UUID  # noqa: TC003 - required at runtime by Pydantic

from pydantic import BaseModel

from pandasync.models import TransportType


class ConnectRequest(BaseModel):
    """Request body for POST /api/v1/connect."""

    source: str
    destination: str
    transport: TransportType = TransportType.AUTO


class ConnectResponse(BaseModel):
    """Response body for POST /api/v1/connect."""

    connection_id: UUID
    source: str
    destination: str
    transport: TransportType
    status: str = "connected"


class DisconnectRequest(BaseModel):
    """Request body for POST /api/v1/disconnect."""

    connection_id: UUID


class DisconnectResponse(BaseModel):
    """Response body for POST /api/v1/disconnect."""

    connection_id: UUID
    status: str = "disconnected"


class StatusResponse(BaseModel):
    """Response body for GET /api/v1/status."""

    version: str
    clock_status: str
    clock_role: str
    clock_offset_us: float
    active_connections: int
    uptime_seconds: float
