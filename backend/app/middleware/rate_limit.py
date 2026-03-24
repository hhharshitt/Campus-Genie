"""
CampusGenie — Rate Limiting Middleware
Prevents API abuse with a simple in-memory sliding window rate limiter.
Limits are applied per client IP address.
"""

import time
import logging
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter.

    Tracks request timestamps per IP in a deque.
    On each request, evicts timestamps older than the window,
    then checks if the count exceeds the limit.

    Default: 60 requests per 60 seconds per IP.
    Upload endpoint: 10 requests per 60 seconds (more expensive).
    """

    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.upload_limit = 10
        self.window_seconds = 60
        # ip -> deque of timestamps
        self._request_log: dict[str, deque] = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        # Respect X-Forwarded-For if behind a proxy
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, ip: str, path: str) -> tuple[bool, int]:
        """
        Returns (is_limited, retry_after_seconds).
        """
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._request_log[ip]

        # Evict old entries
        while timestamps and timestamps[0] < window_start:
            timestamps.popleft()

        limit = self.upload_limit if "upload" in path else self.requests_per_minute
        count = len(timestamps)

        if count >= limit:
            oldest = timestamps[0]
            retry_after = int(self.window_seconds - (now - oldest)) + 1
            return True, retry_after

        timestamps.append(now)
        return False, 0

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and docs
        if request.url.path in {"/api/health", "/docs", "/openapi.json", "/redoc", "/"}:
            return await call_next(request)

        ip = self._get_client_ip(request)
        is_limited, retry_after = self._is_rate_limited(ip, request.url.path)

        if is_limited:
            logger.warning(
                "Rate limit exceeded",
                extra={"client_ip": ip, "path": request.url.path},
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded. Please slow down.",
                    "retry_after_seconds": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        return await call_next(request)
