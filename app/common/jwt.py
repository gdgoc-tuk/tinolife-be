"""JWT 토큰 생성 및 검증 유틸리티"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import settings


class TokenData(BaseModel):
    """JWT 토큰 페이로드 데이터"""
    user_id: int
    email: str


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    JWT 액세스 토큰 생성
    
    Args:
        data: 토큰에 포함할 데이터 (user_id, email 등)
        expires_delta: 토큰 만료 시간 (기본값: 30분)
        
    Returns:
        str: JWT 액세스 토큰
        
    Example:
        >>> token = create_access_token({"user_id": 1, "email": "user@test.com"})
        >>> print(token[:10])
        eyJhbGciOi...
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    JWT 토큰 검증 및 페이로드 추출
    
    Args:
        token: JWT 액세스 토큰
        
    Returns:
        TokenData: 토큰에 포함된 사용자 정보
        None: 토큰이 유효하지 않은 경우
        
    Example:
        >>> token = create_access_token({"user_id": 1, "email": "user@test.com"})
        >>> data = verify_token(token)
        >>> print(data.user_id)
        1
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: int = payload.get("user_id")
        email: str = payload.get("email")
        
        if user_id is None or email is None:
            return None
        
        return TokenData(user_id=user_id, email=email)
        
    except JWTError:
        return None


def decode_token(token: str) -> Optional[dict]:
    """
    JWT 토큰 디코드 (검증 없이 페이로드만 추출)
    
    Args:
        token: JWT 액세스 토큰
        
    Returns:
        dict: 토큰 페이로드
        None: 디코드 실패 시
        
    Note:
        보안이 필요한 경우 verify_token()을 사용하세요.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": False}
        )
        return payload
    except JWTError:
        return None
