from typing import Optional
from datetime import datetime, timedelta
from app.domains.auth.schema import LoginRequest, LoginResponse, TokenData
from app.core.config import settings


class AuthService:
    """인증 비즈니스 로직을 처리하는 서비스"""

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """비밀번호 검증"""
        # TODO: bcrypt 또는 passlib 사용하여 구현
        pass

    def hash_password(self, password: str) -> str:
        """비밀번호 해시"""
        # TODO: bcrypt 또는 passlib 사용하여 구현
        pass

    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """액세스 토큰 생성"""
        # TODO: JWT 토큰 생성 구현
        pass

    def decode_token(self, token: str) -> TokenData:
        """토큰 디코딩 및 검증"""
        # TODO: JWT 토큰 디코딩 구현
        pass

    async def authenticate_user(self, login_data: LoginRequest) -> Optional[LoginResponse]:
        """사용자 인증"""
        # TODO: 데이터베이스 연동 후 구현
        # 1. 이메일로 사용자 조회
        # 2. 비밀번호 검증
        # 3. 액세스 토큰 생성
        # 4. 로그인 응답 반환
        pass

    async def get_current_user(self, token: str) -> TokenData:
        """현재 인증된 사용자 정보 조회"""
        # TODO: 토큰에서 사용자 정보 추출
        pass


# 싱글톤 인스턴스
auth_service = AuthService()
