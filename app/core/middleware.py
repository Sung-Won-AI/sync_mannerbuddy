from time import perf_counter
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id

        started_at = perf_counter()
        response = await call_next(request)
        processing_time_ms = round((perf_counter() - started_at) * 1000)

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Processing-Time-MS"] = str(processing_time_ms)
        return response
