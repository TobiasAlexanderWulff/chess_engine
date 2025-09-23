from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger(__name__)


class RequestIDLoggingMiddleware(BaseHTTPMiddleware):
    """Assign a request ID, log request/response, and attach header."""

    async def dispatch(self, request: Request, call_next: Callable):
        start = time.perf_counter()
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        logger.info(
            "request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
            },
        )

        response = await call_next(request)
        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["x-request-id"] = request_id

        logger.info(
            "response",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response
