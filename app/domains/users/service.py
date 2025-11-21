from typing import List, Optional
from app.domains.users.schema import UserCreate, UserResponse


class UserService:
    """사용자 비즈니스 로직을 처리하는 서비스"""

    async def get_user_by_id(self, user_id: int) -> Optional[UserResponse]:
        """ID로 사용자 조회"""
        # TODO: 데이터베이스 연동 후 구현
        pass

    async def get_user_by_email(self, email: str) -> Optional[UserResponse]:
        """이메일로 사용자 조회"""
        # TODO: 데이터베이스 연동 후 구현
        pass

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[UserResponse]:
        """사용자 목록 조회"""
        # TODO: 데이터베이스 연동 후 구현
        return []

    async def create_user(self, user_data: UserCreate) -> UserResponse:
        """사용자 생성"""
        # TODO: 데이터베이스 연동 후 구현
        pass

    async def update_user(self, user_id: int, user_data: dict) -> Optional[UserResponse]:
        """사용자 정보 업데이트"""
        # TODO: 데이터베이스 연동 후 구현
        pass

    async def delete_user(self, user_id: int) -> bool:
        """사용자 삭제"""
        # TODO: 데이터베이스 연동 후 구현
        pass


# 싱글톤 인스턴스
user_service = UserService()
