"""Security headers middleware for production deployment."""
from __future__ import annotations

from typing import Mapping, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

__all__ = ["SecurityHeadersMiddleware"]


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    DEFAULT_HEADERS: Mapping[str, str] = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
    }

    def __init__(
        self,
        app: ASGIApp,
        content_security_policy: Optional[str] = None,
        strict_transport_security: Optional[str] = None,
        additional_headers: Optional[Mapping[str, str]] = None,
    ) -> None:
        super().__init__(app)
        self._headers = dict(self.DEFAULT_HEADERS)

        if content_security_policy:
            self._headers["Content-Security-Policy"] = content_security_policy

        if strict_transport_security:
            self._headers["Strict-Transport-Security"] = strict_transport_security

        if additional_headers:
            self._headers.update(additional_headers)

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response: Response = await call_next(request)

        for header, value in self._headers.items():
            # Don't override if already set
            if header not in response.headers:
                response.headers[header] = value

        return response
