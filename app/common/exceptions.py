from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Union


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
            }
        },
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "Internal server error",
            }
        },
    )
