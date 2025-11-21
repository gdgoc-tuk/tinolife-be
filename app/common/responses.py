from pydantic import BaseModel
from typing import Optional, Any


class SuccessResponse(BaseModel):
    """성공 응답 모델"""
    success: bool = True
    data: Any
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """에러 응답 모델"""
    success: bool = False
    error: dict
    message: Optional[str] = None
