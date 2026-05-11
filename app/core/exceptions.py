# app/core/exceptions.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(
    request: Request,
    exception: StarletteHTTPException,
):
    return JSONResponse(
        status_code=exception.status_code,
        content={
            "success": False,
            "error": {
                "code": exception.status_code,
                "message": (
                    exception.detail
                    if exception.detail
                    else "An unexpected error occurred."
                ),
            },
        },
    )


async def validation_exception_handler(
    request: Request,
    exception: RequestValidationError,
):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "message": "Validation error",
                "details": exception.errors(),
            },
        },
    )