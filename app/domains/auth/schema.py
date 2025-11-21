from pydantic import BaseModel, EmailStr


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
