from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.domains.auth.schema import (
    LoginRequest, 
    LoginResponse,
    AllowedEmailDomainCreate,
    AllowedEmailDomainUpdate,
    AllowedEmailDomainResponse,
    DomainCheckRequest,
    DomainCheckResponse,
    SendVerificationCodeRequest,
    SendVerificationCodeResponse,
    VerifyCodeRequest,
    VerifyCodeResponse
)
from app.domains.users.schema import SignupRequest, SignupResponse
from app.domains.users.service import get_user_service, UserService
from app.domains.auth.service import (
    get_auth_service,
    get_allowed_email_domain_service,
    get_email_verification_service,
    AuthService,
    AllowedEmailDomainService,
    EmailVerificationService
)
from app.common.email import get_email_service, EmailService
from app.common.exceptions import BadRequestException
from app.common.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    사용자 로그인
    
    - **email**: 이메일 주소
    - **password**: 비밀번호
    
    Returns:
        액세스 토큰과 사용자 정보
        
    Raises:
        - 401: 이메일 또는 비밀번호 불일치
    """
    result = auth_service.authenticate_user(db, login_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 일치하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return result


@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    사용자 로그아웃
    
    토큰을 무효화합니다.
    """
    # TODO: 토큰 블랙리스트 구현
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """
    현재 인증된 사용자 정보 조회
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    
    Returns:
        현재 로그인한 사용자의 정보
        
    Raises:
        - 401: 유효하지 않은 토큰
        - 403: 비활성화된 계정
    """
    from app.domains.users.schema import UserResponse
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname,
        grade=current_user.grade,
        major_id=current_user.major_id,
        is_active=current_user.is_active,
        is_email_verified=current_user.is_email_verified,
        created_at=current_user.created_at
    )


@router.post("/check-domain", response_model=DomainCheckResponse)
async def check_email_domain(
    request: DomainCheckRequest,
    db: Session = Depends(get_db),
    service: AllowedEmailDomainService = Depends(get_allowed_email_domain_service)
):
    """
    이메일 도메인이 허용되는지 확인
    
    - **email**: 검증할 이메일 주소
    
    Returns:
        허용 여부 및 대학교 정보
    """
    result = await service.check_domain_allowed(db, request.email)
    return result


@router.get("/allowed-domains", response_model=List[AllowedEmailDomainResponse])
async def get_allowed_domains(
    active_only: bool = Query(True, description="활성화된 도메인만 조회"),
    db: Session = Depends(get_db),
    service: AllowedEmailDomainService = Depends(get_allowed_email_domain_service)
):
    """
    허용된 이메일 도메인 목록 조회
    
    - **active_only**: 활성화된 도메인만 조회 여부
    """
    domains = await service.get_allowed_domains(db, active_only=active_only)
    return domains


@router.get("/allowed-domains/{domain_id}", response_model=AllowedEmailDomainResponse)
async def get_allowed_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    service: AllowedEmailDomainService = Depends(get_allowed_email_domain_service)
):
    """
    특정 허용 도메인 조회
    
    - **domain_id**: 도메인 ID
    """
    domain = await service.get_domain_by_id(db, domain_id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    return domain


@router.post("/allowed-domains", response_model=AllowedEmailDomainResponse, status_code=status.HTTP_201_CREATED)
async def create_allowed_domain(
    domain_data: AllowedEmailDomainCreate,
    db: Session = Depends(get_db),
    service: AllowedEmailDomainService = Depends(get_allowed_email_domain_service)
):
    """
    새 허용 도메인 추가
    
    - **domain**: 이메일 도메인 (@ 포함 또는 생략 가능)
    - **university_name**: 대학교 이름 (선택)
    """
    # 중복 체크
    domain = domain_data.domain if domain_data.domain.startswith("@") else "@" + domain_data.domain
    existing = await service.get_domain_by_name(db, domain)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Domain already exists"
        )
    
    new_domain = await service.create_allowed_domain(db, domain_data)
    return new_domain


@router.put("/allowed-domains/{domain_id}", response_model=AllowedEmailDomainResponse)
async def update_allowed_domain(
    domain_id: int,
    domain_data: AllowedEmailDomainUpdate,
    db: Session = Depends(get_db),
    service: AllowedEmailDomainService = Depends(get_allowed_email_domain_service)
):
    """
    허용 도메인 정보 업데이트
    
    - **domain_id**: 도메인 ID
    """
    domain = await service.update_allowed_domain(db, domain_id, domain_data)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )
    return domain


@router.delete("/allowed-domains/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_allowed_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    service: AllowedEmailDomainService = Depends(get_allowed_email_domain_service)
):
    """
    허용 도메인 삭제 (소프트 삭제)
    
    - **domain_id**: 도메인 ID
    """
    success = await service.delete_allowed_domain(db, domain_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found"
        )


@router.post("/send-verification-code", response_model=SendVerificationCodeResponse)
async def send_verification_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db),
    domain_service: AllowedEmailDomainService = Depends(get_allowed_email_domain_service),
    verification_service: EmailVerificationService = Depends(get_email_verification_service),
    email_service: EmailService = Depends(get_email_service)
):
    """
    이메일 인증 코드 전송
    
    1. 이메일 도메인 검증 (허용된 도메인인지 확인)
    2. 인증 코드 생성
    3. 이메일 전송
    
    - **email**: 인증할 이메일 주소
    
    Returns:
        전송 성공 여부 및 만료 시간 정보
        
    Raises:
        - 400: 허용되지 않은 도메인
        - 400: 재전송 제한 초과
    """
    try:
        # 1. 도메인 검증
        domain_check = await domain_service.check_domain_allowed(db, request.email)
        if not domain_check.is_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="허용되지 않은 이메일 도메인입니다."
            )
        
        # 2. 인증 코드 생성
        verification = verification_service.create_verification_code(db, request.email)
        
        # 3. 이메일 전송
        email_sent = email_service.send_verification_code(
            to_email=request.email,
            code=verification.code,
            expires_minutes=verification_service.CODE_EXPIRE_MINUTES
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="이메일 전송에 실패했습니다. 잠시 후 다시 시도해주세요."
            )
        
        return SendVerificationCodeResponse(
            success=True,
            message="인증 코드가 이메일로 전송되었습니다.",
            expires_in_minutes=verification_service.CODE_EXPIRE_MINUTES,
            resend_count=verification.resend_count,
            max_resend_count=verification_service.MAX_RESEND_COUNT
        )
        
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )


@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db),
    verification_service: EmailVerificationService = Depends(get_email_verification_service)
):
    """
    이메일 인증 코드 검증
    
    - **email**: 인증할 이메일 주소
    - **code**: 6자리 인증 코드
    
    Returns:
        인증 성공 여부
        
    Raises:
        - 400: 유효하지 않은 코드
        - 400: 만료된 코드
        - 400: 최대 시도 횟수 초과
    """
    try:
        verified = verification_service.verify_code(db, request.email, request.code)
        
        if verified:
            return VerifyCodeResponse(
                success=True,
                message="이메일 인증이 완료되었습니다.",
                verified=True
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="인증에 실패했습니다."
            )
            
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db),
    verification_service: EmailVerificationService = Depends(get_email_verification_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    회원가입
    
    1. 이메일 인증 완료 여부 확인
    2. 사용자 생성 (비밀번호 해싱, 프로필 정보 저장)
    3. 관심사 연결 (선택적)
    
    - **email**: 이메일 주소 (인증 완료된 이메일이어야 함)
    - **password**: 비밀번호 (최소 8자)
    - **nickname**: 닉네임 (2-50자)
    - **grade**: 학년 (1-4)
    - **major_id**: 전공 ID
    - **interest_ids**: 관심사 ID 목록 (선택적)
    - **privacy_policy_agreed**: 개인정보 처리방침 동의 (필수)
    
    Returns:
        생성된 사용자 정보
        
    Raises:
        - 400: 이메일 미인증
        - 400: 이메일 중복
        - 400: 개인정보 미동의
        - 404: 존재하지 않는 major_id
    """
    try:
        # 1. 이메일 인증 완료 여부 확인
        if not verification_service.is_email_verified(db, request.email):
            raise BadRequestException("이메일 인증이 완료되지 않았습니다. 먼저 이메일 인증을 진행해주세요.")
        
        # 2. 사용자 생성
        user = user_service.signup(db, request)
        
        # 3. 응답 반환
        return SignupResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname,
            message="회원가입이 완료되었습니다."
        )
        
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
    except HTTPException:
        raise
    except Exception as e:
        # 예상치 못한 에러 (DB 제약조건 위반 등)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회원가입 처리 중 오류가 발생했습니다: {str(e)}"
        )
