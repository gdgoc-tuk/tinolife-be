from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# ============================================
# AllowedEmailDomain Schemas
# ============================================

class AllowedEmailDomainBase(BaseModel):
    """허용 이메일 도메인 기본 스키마"""
    domain: str = Field(..., min_length=1, max_length=100, description="이메일 도메인 (예: @tukorea.ac.kr)")
    university_name: Optional[str] = Field(None, max_length=100, description="대학교 이름")


class AllowedEmailDomainCreate(AllowedEmailDomainBase):
    """허용 이메일 도메인 생성 스키마"""
    pass


class AllowedEmailDomainUpdate(BaseModel):
    """허용 이메일 도메인 업데이트 스키마"""
    domain: Optional[str] = Field(None, min_length=1, max_length=100)
    university_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class AllowedEmailDomainResponse(AllowedEmailDomainBase):
    """허용 이메일 도메인 응답 스키마"""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class DomainCheckRequest(BaseModel):
    """도메인 검증 요청 스키마"""
    email: EmailStr


class DomainCheckResponse(BaseModel):
    """도메인 검증 응답 스키마"""
    is_allowed: bool
    domain: Optional[str] = None
    university_name: Optional[str] = None


# ============================================
# Auth Schemas
# ============================================

class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """로그인 응답 스키마"""
    access_token: str
    token_type: str = "bearer"
    user_id: int


class TokenData(BaseModel):
    """토큰 데이터 스키마"""
    user_id: int
    email: str


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청 스키마"""
    refresh_token: str
