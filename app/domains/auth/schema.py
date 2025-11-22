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

    model_config = {"from_attributes": True}


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


class SendVerificationCodeRequest(BaseModel):
    """인증 코드 전송 요청 스키마"""
    email: EmailStr = Field(..., description="인증할 이메일 주소")


class SendVerificationCodeResponse(BaseModel):
    """인증 코드 전송 응답 스키마"""
    success: bool
    message: str
    expires_in_minutes: int = Field(..., description="만료 시간 (분)")
    resend_count: int = Field(0, description="재전송 횟수")
    max_resend_count: int = Field(3, description="최대 재전송 횟수")


class VerifyCodeRequest(BaseModel):
    """인증 코드 검증 요청 스키마"""
    email: EmailStr = Field(..., description="인증할 이메일 주소")
    code: str = Field(..., min_length=6, max_length=6, description="6자리 인증 코드")


class VerifyCodeResponse(BaseModel):
    """인증 코드 검증 응답 스키마"""
    success: bool
    message: str
    verified: bool = Field(..., description="인증 성공 여부")


class VerificationStatusResponse(BaseModel):
    """인증 상태 조회 응답 스키마"""
    email: EmailStr
    is_verified: bool
    expires_at: Optional[datetime] = None
    attempt_count: int = 0
    resend_count: int = 0
    created_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}
