from typing import Optional, List
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.domains.auth.schema import (
    LoginRequest,
    LoginResponse,
    TokenData,
    AllowedEmailDomainCreate,
    AllowedEmailDomainUpdate,
    DomainCheckResponse,
)
from app.domains.auth.model import AllowedEmailDomain, EmailVerification
from app.common.utils import generate_verification_code
from app.common.exceptions import BadRequestException


class AllowedEmailDomainService:
    """허용 이메일 도메인 관리 서비스"""

    async def check_domain_allowed(
        self, db: Session, email: str
    ) -> DomainCheckResponse:
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
        allowed_domain = (
            db.query(AllowedEmailDomain)
            .filter(
                AllowedEmailDomain.domain == domain,
                AllowedEmailDomain.is_active.is_(True),
            )
            .first()
        )

        if allowed_domain:
            return DomainCheckResponse(
                is_allowed=True,
                domain=allowed_domain.domain,
                university_name=allowed_domain.university_name,
            )

        return DomainCheckResponse(is_allowed=False)

    async def get_allowed_domains(
        self, db: Session, active_only: bool = True
    ) -> List[AllowedEmailDomain]:
        """허용 도메인 목록 조회"""
        query = db.query(AllowedEmailDomain)

        if active_only:
            query = query.filter(AllowedEmailDomain.is_active.is_(True))

        return query.order_by(AllowedEmailDomain.university_name).all()

    async def get_domain_by_id(
        self, db: Session, domain_id: int
    ) -> Optional[AllowedEmailDomain]:
        """ID로 도메인 조회"""
        return (
            db.query(AllowedEmailDomain)
            .filter(AllowedEmailDomain.id == domain_id)
            .first()
        )

    async def get_domain_by_name(
        self, db: Session, domain: str
    ) -> Optional[AllowedEmailDomain]:
        """도메인명으로 조회"""
        return (
            db.query(AllowedEmailDomain)
            .filter(AllowedEmailDomain.domain == domain)
            .first()
        )

    async def create_allowed_domain(
        self, db: Session, domain_data: AllowedEmailDomainCreate
    ) -> AllowedEmailDomain:
        """허용 도메인 생성"""
        # @ 자동 추가
        domain = domain_data.domain
        if not domain.startswith("@"):
            domain = "@" + domain

        allowed_domain = AllowedEmailDomain(
            domain=domain, university_name=domain_data.university_name
        )
        db.add(allowed_domain)
        db.commit()
        db.refresh(allowed_domain)
        return allowed_domain

    async def update_allowed_domain(
        self, db: Session, domain_id: int, domain_data: AllowedEmailDomainUpdate
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

    async def delete_allowed_domain(self, db: Session, domain_id: int) -> bool:
        """허용 도메인 삭제 (소프트 삭제)"""
        allowed_domain = await self.get_domain_by_id(db, domain_id)
        if not allowed_domain:
            return False

        allowed_domain.is_active = False
        db.commit()
        return True


class AuthService:
    """인증 비즈니스 로직을 처리하는 서비스"""

    def authenticate_user(
        self, db: Session, login_data: LoginRequest
    ) -> Optional[LoginResponse]:
        """
        사용자 인증 및 JWT 토큰 생성

        Args:
            db: 데이터베이스 세션
            login_data: 로그인 요청 데이터 (email, password)

        Returns:
            LoginResponse: 액세스 토큰 및 사용자 정보
            None: 인증 실패 시
        """
        from app.domains.users.service import UserService
        from app.common.security import verify_password
        from app.common.jwt import create_access_token

        user_service = UserService()

        # 1. 이메일로 사용자 조회
        user = user_service.get_user_by_email(db, login_data.email)
        if not user:
            return None

        # 2. 비밀번호 검증
        if not verify_password(login_data.password, user.hashed_password):
            return None

        # 3. 액세스 토큰 생성
        access_token = create_access_token(
            data={"user_id": user.id, "email": user.email}
        )

        # 4. 로그인 응답 반환
        return LoginResponse(
            access_token=access_token, token_type="bearer", user_id=user.id
        )

    def get_current_user_from_token(self, token: str) -> Optional[TokenData]:
        """
        JWT 토큰에서 현재 사용자 정보 추출

        Args:
            token: JWT 액세스 토큰

        Returns:
            TokenData: 토큰에 포함된 사용자 정보
            None: 토큰이 유효하지 않은 경우
        """
        from app.common.jwt import verify_token

        return verify_token(token)
        # TODO: 토큰에서 사용자 정보 추출
        pass


def get_allowed_email_domain_service() -> AllowedEmailDomainService:
    """AllowedEmailDomainService 의존성 주입"""
    return AllowedEmailDomainService()


def get_auth_service() -> AuthService:
    """AuthService 의존성 주입"""
    return AuthService()


class EmailVerificationService:
    """이메일 인증 비즈니스 로직을 처리하는 서비스"""

    # 상수 정의
    CODE_EXPIRE_MINUTES = 5  # 인증 코드 유효 시간 (분)
    MAX_ATTEMPT_COUNT = 5  # 최대 시도 횟수
    MAX_RESEND_COUNT = 3  # 최대 재전송 횟수
    RESEND_COOLDOWN_SECONDS = 60  # 재전송 쿨다운 (초)

    def create_verification_code(self, db: Session, email: str) -> EmailVerification:
        """
        새로운 인증 코드를 생성하고 저장합니다.

        Args:
            db: 데이터베이스 세션
            email: 이메일 주소

        Returns:
            EmailVerification: 생성된 인증 레코드

        Raises:
            BadRequestException: 재전송 제한 초과 시
        """
        # 기존 미인증 코드 조회
        existing = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.email == email, EmailVerification.is_verified.is_(False)
            )
            .order_by(EmailVerification.created_at.desc())
            .first()
        )

        # 재전송 제한 체크
        if existing:
            # 최대 재전송 횟수 초과 체크
            if existing.resend_count >= self.MAX_RESEND_COUNT:
                raise BadRequestException(
                    f"재전송 횟수를 초과했습니다. {self.CODE_EXPIRE_MINUTES}분 후 다시 시도해주세요."
                )

            # 쿨다운 시간 체크
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            created_naive = existing.created_at.replace(tzinfo=None)
            time_since_created = now_naive - created_naive
            if time_since_created.total_seconds() < self.RESEND_COOLDOWN_SECONDS:
                remaining = self.RESEND_COOLDOWN_SECONDS - int(
                    time_since_created.total_seconds()
                )
                raise BadRequestException(f"{remaining}초 후에 재전송할 수 있습니다.")

            # 기존 레코드의 재전송 카운트 증가
            existing.resend_count += 1
            db.commit()

        # 새 인증 코드 생성
        code = generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=self.CODE_EXPIRE_MINUTES
        )

        verification = EmailVerification(
            email=email,
            code=code,
            expires_at=expires_at,
            is_verified=False,
            attempt_count=0,
            resend_count=existing.resend_count if existing else 0,
        )

        db.add(verification)
        db.commit()
        db.refresh(verification)

        return verification

    def verify_code(self, db: Session, email: str, code: str) -> bool:
        """
        인증 코드를 검증합니다.

        Args:
            db: 데이터베이스 세션
            email: 이메일 주소
            code: 인증 코드

        Returns:
            bool: 인증 성공 여부

        Raises:
            BadRequestException: 인증 실패 시
        """
        # 최신 미인증 코드 조회
        verification = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.email == email, EmailVerification.is_verified.is_(False)
            )
            .order_by(EmailVerification.created_at.desc())
            .first()
        )

        if not verification:
            raise BadRequestException("유효한 인증 요청이 없습니다.")

        # 시도 횟수 증가
        verification.attempt_count += 1
        db.commit()

        # 최대 시도 횟수 초과 체크
        if verification.attempt_count > self.MAX_ATTEMPT_COUNT:
            raise BadRequestException(
                f"최대 시도 횟수({self.MAX_ATTEMPT_COUNT}회)를 초과했습니다. 새로운 인증 코드를 요청해주세요."
            )

        # 만료 시간 체크
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        expires_naive = verification.expires_at.replace(tzinfo=None)
        if now_naive > expires_naive:
            raise BadRequestException(
                "인증 코드가 만료되었습니다. 새로운 인증 코드를 요청해주세요."
            )

        # 코드 일치 여부 체크
        if verification.code != code:
            remaining_attempts = self.MAX_ATTEMPT_COUNT - verification.attempt_count
            if remaining_attempts > 0:
                raise BadRequestException(
                    f"인증 코드가 일치하지 않습니다. (남은 시도: {remaining_attempts}회)"
                )
            else:
                raise BadRequestException(
                    "최대 시도 횟수를 초과했습니다. 새로운 인증 코드를 요청해주세요."
                )

        # 인증 성공
        verification.is_verified = True
        db.commit()

        return True

    def is_email_verified(self, db: Session, email: str) -> bool:
        """
        이메일이 인증되었는지 확인합니다.

        Args:
            db: 데이터베이스 세션
            email: 이메일 주소

        Returns:
            bool: 인증 여부
        """
        verified = (
            db.query(EmailVerification)
            .filter(
                EmailVerification.email == email, EmailVerification.is_verified.is_(True)
            )
            .first()
        )

        return verified is not None

    def get_verification_status(
        self, db: Session, email: str
    ) -> Optional[EmailVerification]:
        """
        이메일의 인증 상태를 조회합니다.

        Args:
            db: 데이터베이스 세션
            email: 이메일 주소

        Returns:
            Optional[EmailVerification]: 최신 인증 레코드
        """
        return (
            db.query(EmailVerification)
            .filter(EmailVerification.email == email)
            .order_by(EmailVerification.created_at.desc())
            .first()
        )


def get_email_verification_service() -> EmailVerificationService:
    """EmailVerificationService 의존성 주입"""
    return EmailVerificationService()
