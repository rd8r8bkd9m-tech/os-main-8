"""Application factory for the Kolibri FastAPI service."""
from __future__ import annotations

import os
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .exception_handlers import register_exception_handlers
from .lifespan import lifespan
from .middlewares import RequestContextMiddleware
from .rate_limit import RateLimitMiddleware
from .routes import api_router
from .security_headers import SecurityHeadersMiddleware

__all__ = ["create_app", "app"]


def _get_cors_origins() -> List[str]:
    """Get allowed CORS origins from environment or use defaults."""
    env_origins = os.getenv("KOLIBRI_CORS_ORIGINS")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]
    # Default development origins
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]


def _is_production() -> bool:
    """Check if running in production mode."""
    env = os.getenv("KOLIBRI_ENV", "development").lower()
    return env in ("production", "prod")


def _parse_env_bool(name: str, default: bool = False) -> bool:
    """Parse boolean value from environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")


def create_app() -> FastAPI:
    # Validate settings on startup to fail fast on configuration errors
    get_settings()
    is_prod = _is_production()

    application = FastAPI(
        title="Kolibri Enterprise API",
        version="1.0.0",
        description="Production-ready AI reasoning and knowledge platform",
        lifespan=lifespan,
        # Disable docs in production for security
        docs_url=None if is_prod else "/docs",
        redoc_url=None if is_prod else "/redoc",
        openapi_url=None if is_prod else "/openapi.json",
    )

    # Register global exception handlers
    register_exception_handlers(application)

    # Security headers middleware (outermost - applied last)
    hsts = "max-age=31536000; includeSubDomains" if is_prod else None
    application.add_middleware(
        SecurityHeadersMiddleware,
        strict_transport_security=hsts,
    )

    # Rate limiting middleware
    rate_limit_enabled = _parse_env_bool("KOLIBRI_RATE_LIMIT_ENABLED", default=True)
    rps = float(os.getenv("KOLIBRI_RATE_LIMIT_RPS", "30"))
    burst = float(os.getenv("KOLIBRI_RATE_LIMIT_BURST", "60"))
    application.add_middleware(
        RateLimitMiddleware,
        requests_per_second=rps,
        burst_size=burst,
        enabled=rate_limit_enabled,
    )

    # CORS middleware
    cors_origins = _get_cors_origins()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "Retry-After"],
        max_age=600,  # 10 minutes preflight cache
    )

    # Request context middleware (innermost - applied first)
    application.add_middleware(RequestContextMiddleware)

    application.include_router(api_router)
    application.add_event_handler("shutdown", get_settings.cache_clear)

    return application


app = create_app()
