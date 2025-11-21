from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """사용자 기본 스키마"""
    email: EmailStr
    nickname: str = Field(..., min_length=2, max_length=20, description="닉네임")


class SignupRequest(BaseModel):
    """회원가입 요청 스키마"""
    email: EmailStr = Field(..., description="대학 이메일")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    nickname: str = Field(..., min_length=2, max_length=20, description="닉네임")
    grade: int = Field(..., ge=1, le=4, description="학년 (1-4)")
    major_id: int = Field(..., description="전공 ID")
    interest_ids: Optional[List[int]] = Field(default=[], description="관심사 ID 목록 (선택)")
    privacy_policy_agreed: bool = Field(..., description="개인정보 처리방침 동의")


class SignupResponse(BaseModel):
    """회원가입 응답 스키마"""
    id: int
    email: EmailStr
    nickname: str
    message: str = "회원가입이 완료되었습니다."


class UserCreate(BaseModel):
    """내부 사용자 생성 스키마"""
    email: EmailStr
    hashed_password: str
    nickname: str
    grade: int
    major_id: int
    is_email_verified: bool = True


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
