"""
CampusGenie — Request Logging Middleware
Logs every HTTP request with method, path, status code, and duration.
Attaches a unique request_id to each request for traceability.
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs incoming requests and outgoing responses.

    Each request gets a UUID (request_id) that appears in both the
    request log and response log — makes it easy to correlate entries.
    """

    # Paths to skip logging (health checks would spam the logs)
    SKIP_PATHS = {"/api/health", "/", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Attach request_id to request state so routes can access it
        request.state.request_id = request_id

        skip = request.url.path in self.SKIP_PATHS

        if not skip:
            logger.info(
                "Request started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host if request.client else "unknown",
                },
            )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.error(
                "Request failed with unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "error": str(exc),
                },
                exc_info=True,
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        if not skip:
            level = logging.WARNING if response.status_code >= 400 else logging.INFO
            logger.log(
                level,
                "Request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                },
            )

        # Pass request_id back in response header for client-side debugging
        response.headers["X-Request-ID"] = request_id
        return response
