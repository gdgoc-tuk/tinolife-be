from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


class UserInDB(UserBase):
    """데이터베이스 사용자 스키마"""
    id: int
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
