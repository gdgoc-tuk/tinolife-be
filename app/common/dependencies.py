"""인증 관련 의존성"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.auth.service import AuthService, get_auth_service
from app.domains.users.model import User
from app.domains.users.service import UserService, get_user_service


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
) -> User:
    """
    현재 인증된 사용자 조회
    
    Args:
        credentials: Bearer 토큰
        db: 데이터베이스 세션
        auth_service: 인증 서비스
        user_service: 사용자 서비스
        
    Returns:
        User: 현재 인증된 사용자 객체
        
    Raises:
        HTTPException 401: 토큰이 유효하지 않거나 사용자를 찾을 수 없음
    """
    token = credentials.credentials
    
    # JWT 토큰 검증 및 사용자 정보 추출
    token_data = auth_service.get_current_user_from_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 정보입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 데이터베이스에서 사용자 조회
    user = user_service.get_user_by_id(db, token_data.user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 비활성화된 사용자 체크
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다.",
        )
    
    return user
