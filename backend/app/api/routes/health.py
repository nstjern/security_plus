"""Liveness and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.schemas import HealthResponse, ReadinessResponse
from app.core.constants import API_VERSION
from app.db.session import database_is_reachable

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse, summary="Liveness probe")
def healthz() -> HealthResponse:
    """Report that the process is running. Deliberately does not touch the database."""
    return HealthResponse(status="ok", version=API_VERSION)


@router.get("/readyz", response_model=ReadinessResponse, summary="Readiness probe")
def readyz(response: Response) -> ReadinessResponse:
    """Report whether dependencies are available, so orchestrators can delay traffic."""
    reachable = database_is_reachable()
    if not reachable:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ready" if reachable else "degraded",
        database="up" if reachable else "down",
    )
