"""
TalentUP Fichaje — Rate limiting middleware.
In-memory sliding window rate limiter per IP + endpoint.
"""
import time
from collections import defaultdict, deque
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter. Limits per (IP, endpoint_prefix) pair."""

    def __init__(self, app, default_limit: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = defaultdict(deque)

        # Stricter limits for sensitive endpoints
        self.endpoint_limits = {
            "/api/auth/login": 10,       # 10 login attempts per minute
            "/api/clock": 30,            # 30 clock operations per minute
            "/api/clock/nfc": 30,        # 30 NFC clock operations per minute
            "/api/employees": 60,        # 60 employee operations per minute
        }

    def _get_limit(self, path: str) -> int:
        for prefix, limit in self.endpoint_limits.items():
            if path.startswith(prefix):
                return limit
        return self.default_limit

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:{path}"
        limit = self._get_limit(path)
        now = time.monotonic()

        # Clean old entries
        req_deque = self.requests[key]
        while req_deque and req_deque[0] <= now - self.window_seconds:
            req_deque.popleft()

        if len(req_deque) >= limit:
            return Response(
                content='{"detail":"Rate limit exceeded. Intentelo mas tarde."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.window_seconds)},
            )

        req_deque.append(now)
        return await call_next(request)