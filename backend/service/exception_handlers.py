"""Global exception handlers for production deployment."""
from __future__ import annotations

import logging
import traceback
from typing import Any, Dict

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse

__all__ = ["register_exception_handlers"]

_logger = logging.getLogger("kolibri.service.errors")


def _create_error_response(
    status_code: int,
    error: str,
    message: str,
    details: Dict[str, Any] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Create a standardized error response.
    
    Includes both 'detail' for FastAPI compatibility and 'message' for
    enhanced error reporting.
    """
    content: Dict[str, Any] = {
        "error": error,
        "message": message,
        "detail": message,  # FastAPI compatibility
        "status_code": status_code,
    }
    if details:
        content["details"] = details
    if request_id:
        content["request_id"] = request_id

    return JSONResponse(status_code=status_code, content=content)


async def _validation_exception_handler(
    request: Request,
    exc: RequestValidationError | ValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    errors = exc.errors() if hasattr(exc, "errors") else []
    details = []

    for error in errors:
        loc = error.get("loc", ())
        field = ".".join(str(x) for x in loc) if loc else "unknown"
        details.append({
            "field": field,
            "message": error.get("msg", "Validation error"),
            "type": error.get("type", "value_error"),
        })

    _logger.warning(
        "validation_error",
        extra={
            "path": request.url.path,
            "method": request.method,
            "errors": details,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error="VALIDATION_ERROR",
        message="Request validation failed",
        details={"validation_errors": details},
    )


async def _http_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle HTTP exceptions."""
    from fastapi import HTTPException

    if isinstance(exc, HTTPException):
        status_code = exc.status_code
        detail = exc.detail
        headers = getattr(exc, "headers", None)
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        detail = "Internal server error"
        headers = None

    error_code = _status_to_error_code(status_code)

    if status_code >= 500:
        _logger.error(
            "http_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
                "detail": detail,
            },
        )
    else:
        _logger.info(
            "http_error",
            extra={
                "path": request.url.path,
                "method": request.method,
                "status_code": status_code,
            },
        )

    response = _create_error_response(
        status_code=status_code,
        error=error_code,
        message=detail if isinstance(detail, str) else str(detail),
    )

    if headers:
        for key, value in headers.items():
            response.headers[key] = value

    return response


async def _generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle unexpected exceptions."""
    _logger.exception(
        "unhandled_exception",
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        },
    )

    return _create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="INTERNAL_ERROR",
        message="An unexpected error occurred. Please try again later.",
    )


def _status_to_error_code(status_code: int) -> str:
    """Map HTTP status code to error code."""
    mapping = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMITED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }
    return mapping.get(status_code, f"HTTP_{status_code}")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    from fastapi import HTTPException

    app.add_exception_handler(RequestValidationError, _validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(ValidationError, _validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(HTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _generic_exception_handler)  # type: ignore[arg-type]
