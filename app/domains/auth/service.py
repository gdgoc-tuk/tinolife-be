from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.domains.auth.schema import (
    LoginRequest, 
    LoginResponse, 
    TokenData,
    AllowedEmailDomainCreate,
    AllowedEmailDomainUpdate,
    DomainCheckResponse
)
from app.domains.auth.model import AllowedEmailDomain
from app.core.config import settings


class AllowedEmailDomainService:
    """허용 이메일 도메인 관리 서비스"""

    async def check_domain_allowed(self, db: Session, email: str) -> DomainCheckResponse:
        """
        이메일 도메인이 허용되는지 확인
        
        Args:
            db: 데이터베이스 세션
            email: 검증할 이메일 주소
            
        Returns:
            DomainCheckResponse: 허용 여부 및 도메인 정보
        """
        # 이메일에서 도메인 추출 (@ 포함)
        if "@" not in email:
            return DomainCheckResponse(is_allowed=False)
        
        domain = "@" + email.split("@")[1]
        
        # 데이터베이스에서 도메인 조회
        allowed_domain = db.query(AllowedEmailDomain).filter(
            AllowedEmailDomain.domain == domain,
            AllowedEmailDomain.is_active == True
        ).first()
        
        if allowed_domain:
            return DomainCheckResponse(
                is_allowed=True,
                domain=allowed_domain.domain,
                university_name=allowed_domain.university_name
            )
        
        return DomainCheckResponse(is_allowed=False)

    async def get_allowed_domains(
        self, 
        db: Session,
        active_only: bool = True
    ) -> List[AllowedEmailDomain]:
        """허용 도메인 목록 조회"""
        query = db.query(AllowedEmailDomain)
        
        if active_only:
            query = query.filter(AllowedEmailDomain.is_active == True)
        
        return query.order_by(AllowedEmailDomain.university_name).all()

    async def get_domain_by_id(
        self, 
        db: Session, 
        domain_id: int
    ) -> Optional[AllowedEmailDomain]:
        """ID로 도메인 조회"""
        return db.query(AllowedEmailDomain).filter(
            AllowedEmailDomain.id == domain_id
        ).first()

    async def get_domain_by_name(
        self, 
        db: Session, 
        domain: str
    ) -> Optional[AllowedEmailDomain]:
        """도메인명으로 조회"""
        return db.query(AllowedEmailDomain).filter(
            AllowedEmailDomain.domain == domain
        ).first()

    async def create_allowed_domain(
        self, 
        db: Session, 
        domain_data: AllowedEmailDomainCreate
    ) -> AllowedEmailDomain:
        """허용 도메인 생성"""
        # @ 자동 추가
        domain = domain_data.domain
        if not domain.startswith("@"):
            domain = "@" + domain
        
        allowed_domain = AllowedEmailDomain(
            domain=domain,
            university_name=domain_data.university_name
        )
        db.add(allowed_domain)
        db.commit()
        db.refresh(allowed_domain)
        return allowed_domain

    async def update_allowed_domain(
        self, 
        db: Session, 
        domain_id: int, 
        domain_data: AllowedEmailDomainUpdate
    ) -> Optional[AllowedEmailDomain]:
        """허용 도메인 업데이트"""
        allowed_domain = await self.get_domain_by_id(db, domain_id)
        if not allowed_domain:
            return None
        
        update_data = domain_data.model_dump(exclude_unset=True)
        
        # @ 자동 추가
        if "domain" in update_data and update_data["domain"]:
            if not update_data["domain"].startswith("@"):
                update_data["domain"] = "@" + update_data["domain"]
        
        for field, value in update_data.items():
            setattr(allowed_domain, field, value)
        
        db.commit()
        db.refresh(allowed_domain)
        return allowed_domain

    async def delete_allowed_domain(
        self, 
        db: Session, 
        domain_id: int
    ) -> bool:
        """허용 도메인 삭제 (소프트 삭제)"""
        allowed_domain = await self.get_domain_by_id(db, domain_id)
        if not allowed_domain:
            return False
        
        allowed_domain.is_active = False
        db.commit()
        return True


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


def get_allowed_email_domain_service() -> AllowedEmailDomainService:
    """AllowedEmailDomainService 의존성 주입"""
    return AllowedEmailDomainService()


def get_auth_service() -> AuthService:
    """AuthService 의존성 주입"""
    return AuthService()
