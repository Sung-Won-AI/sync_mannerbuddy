from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


async def app_error_handler(
    request: Request,
    exc: AppError,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": _request_id(request),
            }
        },
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_INPUT",
                "message": "요청값을 확인해주세요.",
                "details": {"errors": exc.errors()},
                "request_id": _request_id(request),
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
