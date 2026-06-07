import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import get_logger

logger = get_logger("http_middleware")

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log request metadata, response codes, and latency."""
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)

        logger.info(
            "Incoming request",
            method=method,
            path=path,
            query_params=query_params,
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            logger.info(
                "Request completed",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
            )
            return response
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Request failed",
                method=method,
                path=path,
                error=str(e),
                duration_ms=round(duration_ms, 2),
            )
            raise e
