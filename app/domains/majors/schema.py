from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class MajorBase(BaseModel):
    """전공 기본 스키마"""

    name: str = Field(..., min_length=1, max_length=100, description="전공명")
    code: Optional[str] = Field(None, max_length=20, description="전공 코드")


class MajorCreate(MajorBase):
    """전공 생성 스키마"""

    pass


class MajorUpdate(BaseModel):
    """전공 업데이트 스키마"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    code: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None


class MajorResponse(MajorBase):
    """전공 응답 스키마"""

    id: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
