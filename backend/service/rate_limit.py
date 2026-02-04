"""Rate limiting middleware for production deployment."""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, Optional, Tuple

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

__all__ = ["RateLimitMiddleware", "RateLimiter"]


@dataclass
class TokenBucket:
    """Token bucket implementation for rate limiting."""

    capacity: float
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    last_refill: float = field(init=False)
    lock: Lock = field(default_factory=Lock, repr=False)

    def __post_init__(self) -> None:
        self.tokens = self.capacity
        self.last_refill = time.monotonic()

    def consume(self, tokens: float = 1.0) -> bool:
        """Try to consume tokens. Returns True if successful."""
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_retry_after(self) -> float:
        """Calculate seconds until a token becomes available."""
        with self.lock:
            if self.tokens >= 1.0:
                return 0.0
            return (1.0 - self.tokens) / self.refill_rate


class RateLimiter:
    """In-memory rate limiter using token bucket algorithm."""

    def __init__(
        self,
        requests_per_second: float = 10.0,
        burst_size: float = 20.0,
        cleanup_interval: int = 300,
    ) -> None:
        self._requests_per_second = requests_per_second
        self._burst_size = burst_size
        self._cleanup_interval = cleanup_interval
        self._buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=burst_size, refill_rate=requests_per_second)
        )
        self._last_cleanup = time.monotonic()
        self._lock = Lock()

    def is_allowed(self, key: str) -> Tuple[bool, float]:
        """Check if request is allowed and return (allowed, retry_after)."""
        self._maybe_cleanup()
        bucket = self._buckets[key]
        allowed = bucket.consume()
        retry_after = 0.0 if allowed else bucket.get_retry_after()
        return allowed, retry_after

    def _maybe_cleanup(self) -> None:
        """Periodically clean up stale buckets."""
        now = time.monotonic()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        with self._lock:
            if now - self._last_cleanup < self._cleanup_interval:
                return

            stale_keys = []
            for key, bucket in self._buckets.items():
                if now - bucket.last_refill > self._cleanup_interval:
                    stale_keys.append(key)

            for key in stale_keys:
                del self._buckets[key]

            self._last_cleanup = now


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting requests."""

    # Paths that bypass rate limiting
    EXEMPT_PATHS = frozenset({"/api/health", "/healthz", "/readyz", "/metrics"})

    def __init__(
        self,
        app: ASGIApp,
        limiter: Optional[RateLimiter] = None,
        requests_per_second: float = 30.0,
        burst_size: float = 60.0,
        enabled: bool = True,
    ) -> None:
        super().__init__(app)
        self._limiter = limiter or RateLimiter(
            requests_per_second=requests_per_second,
            burst_size=burst_size,
        )
        self._enabled = enabled

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if not self._enabled:
            return await call_next(request)

        path = request.url.path
        if path in self.EXEMPT_PATHS:
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        allowed, retry_after = self._limiter.is_allowed(client_ip)

        if not allowed:
            from starlette.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={
                    "error": "RATE_LIMITED",
                    "message": "Rate limit exceeded. Please slow down.",
                    "detail": "Rate limit exceeded. Please slow down.",
                },
                headers={"Retry-After": str(int(retry_after) + 1)},
            )

        return await call_next(request)

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP, considering proxy headers."""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain (original client)
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        client = request.client
        return client.host if client else "unknown"
