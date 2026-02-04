"""Health and diagnostics endpoints."""
from __future__ import annotations

import time
from typing import Any, Dict

from fastapi import APIRouter, Depends
from starlette.responses import JSONResponse, Response

from ..config import Settings, get_settings
from ..instrumentation import CONTENT_TYPE_LATEST, generate_latest, registry
from ..schemas import HealthResponse

__all__ = ["router"]

router = APIRouter()

# Track service start time for uptime calculation
_start_time = time.time()


@router.get("/api/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """General health check endpoint."""
    return HealthResponse(
        status="ok",
        response_mode=settings.response_mode,
        sso_enabled=settings.sso_enabled,
        prometheus_namespace=settings.prometheus_namespace,
    )


@router.get("/healthz")
async def healthz() -> Dict[str, Any]:
    """
    Kubernetes liveness probe endpoint.

    This endpoint indicates whether the service is running.
    A failure here triggers container restart.
    """
    return {
        "status": "ok",
        "service": "kolibri-backend",
        "timestamp": time.time(),
    }


@router.get("/readyz")
async def readyz(
    settings: Settings = Depends(get_settings),
) -> JSONResponse:
    """
    Kubernetes readiness probe endpoint.

    This endpoint indicates whether the service is ready to accept traffic.
    Checks critical dependencies before declaring readiness.
    """
    checks: Dict[str, bool] = {}
    ready = True

    # Check configuration is loaded
    try:
        _ = settings.response_mode
        checks["config"] = True
    except Exception:
        checks["config"] = False
        ready = False

    # Check if LLM endpoint is configured when in LLM mode
    if settings.response_mode == "llm":
        llm_configured = bool(settings.llm_endpoint)
        checks["llm_endpoint"] = llm_configured
        if not llm_configured:
            ready = False

    uptime = time.time() - _start_time

    status_code = 200 if ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": ready,
            "checks": checks,
            "uptime_seconds": round(uptime, 2),
        },
    )


@router.get("/api/v1/status")
async def detailed_status(
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """
    Detailed service status for debugging and monitoring.
    Returns comprehensive information about service configuration and state.
    """
    uptime = time.time() - _start_time

    return {
        "service": "kolibri-backend",
        "version": "1.0.0",
        "status": "running",
        "uptime_seconds": round(uptime, 2),
        "configuration": {
            "response_mode": settings.response_mode,
            "sso_enabled": settings.sso_enabled,
            "llm_configured": bool(settings.llm_endpoint),
            "log_level": settings.log_level,
            "prometheus_namespace": settings.prometheus_namespace,
        },
        "features": {
            "rate_limiting": True,
            "security_headers": True,
            "structured_logging": settings.log_json,
            "metrics_enabled": True,
        },
    }


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    payload = generate_latest(registry)
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)
