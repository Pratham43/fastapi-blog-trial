import time

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request,
        call_next,
    ):
        start = time.perf_counter()

        response = await call_next(request)

        elapsed = (
            time.perf_counter() - start
        ) * 1000

        logger.info(
            "{} {} -> {} ({:.2f} ms)",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )

        return response