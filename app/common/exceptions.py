from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class BadRequestException(HTTPException):
    """400 Bad Request 예외"""

    def __init__(self, detail: str = "Bad Request"):
        super().__init__(status_code=400, detail=detail)


class UnauthorizedException(HTTPException):
    """401 Unauthorized 예외"""

    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(status_code=401, detail=detail)


class ForbiddenException(HTTPException):
    """403 Forbidden 예외"""

    def __init__(self, detail: str = "Forbidden"):
        super().__init__(status_code=403, detail=detail)


class NotFoundException(HTTPException):
    """404 Not Found 예외"""

    def __init__(self, detail: str = "Not Found"):
        super().__init__(status_code=404, detail=detail)


class ConflictException(HTTPException):
    """409 Conflict 예외"""

    def __init__(self, detail: str = "Conflict"):
        super().__init__(status_code=409, detail=detail)


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
