"""Application lifespan handlers."""
from __future__ import annotations

import asyncio
import logging
import signal
import threading
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI

from .config import get_settings
from .observability import configure_logging

__all__ = ["lifespan"]

_logger = logging.getLogger("kolibri.service")
_active_connections: Set[asyncio.Task[None]] = set()
_shutdown_event = asyncio.Event()


def _register_shutdown_handlers() -> None:
    """Register signal handlers for graceful shutdown.
    
    Note: Signal handlers can only be registered from the main thread.
    In test environments or non-main threads, this is safely skipped.
    """
    # Only register signal handlers if running in main thread
    if threading.current_thread() is not threading.main_thread():
        return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop yet
        return

    def _signal_handler(sig: signal.Signals) -> None:
        _logger.info(
            "shutdown_signal_received",
            extra={"signal": sig.name},
        )
        _shutdown_event.set()

    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, _signal_handler, sig)
        except (NotImplementedError, ValueError, RuntimeError):
            # Windows doesn't support add_signal_handler
            # ValueError: signal only works in main thread
            # RuntimeError: set_wakeup_fd only works in main thread
            pass


async def _graceful_shutdown(timeout: float = 30.0) -> None:
    """Wait for active connections to complete with timeout."""
    if not _active_connections:
        return

    _logger.info(
        "graceful_shutdown_started",
        extra={"active_connections": len(_active_connections)},
    )

    # Wait for active tasks to complete
    done, pending = await asyncio.wait(
        _active_connections,
        timeout=timeout,
        return_when=asyncio.ALL_COMPLETED,
    )

    if pending:
        _logger.warning(
            "graceful_shutdown_timeout",
            extra={
                "completed": len(done),
                "cancelled": len(pending),
            },
        )
        for task in pending:
            task.cancel()


@asynccontextmanager
async def lifespan(app: FastAPI):  # pragma: no cover - integration behaviour tested
    settings = get_settings()
    configure_logging(settings.log_level, json_logs=settings.log_json)

    _register_shutdown_handlers()

    _logger.info(
        "service_starting",
        extra={
            "log_level": settings.log_level,
            "log_json": settings.log_json,
            "response_mode": settings.response_mode,
            "sso_enabled": settings.sso_enabled,
        },
    )

    try:
        yield
    finally:
        _logger.info("service_shutting_down")
        await _graceful_shutdown()
        _logger.info("service_stopped")
