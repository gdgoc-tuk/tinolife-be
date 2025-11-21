from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class InterestBase(BaseModel):
    """관심사 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=50, description="관심사명")


class InterestCreate(InterestBase):
    """관심사 생성 스키마"""
    pass


class InterestUpdate(BaseModel):
    """관심사 업데이트 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None


class InterestResponse(InterestBase):
    """관심사 응답 스키마"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PaginatedInterestResponse(BaseModel):
    """페이지네이션된 관심사 목록 응답"""
    items: List[InterestResponse]
    total: int
    page: int
    size: int
    total_pages: int
