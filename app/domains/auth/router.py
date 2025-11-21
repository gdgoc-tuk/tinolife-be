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
    DomainCheckResponse
)
from app.domains.auth.service import (
    get_auth_service,
    get_allowed_email_domain_service,
    AuthService,
    AllowedEmailDomainService
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    사용자 로그인
    
    - **email**: 이메일 주소
    - **password**: 비밀번호
    
    Returns:
        액세스 토큰과 사용자 정보
    """
    result = await auth_service.authenticate_user(login_data)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
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
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    현재 인증된 사용자 정보 조회
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    """
    token = credentials.credentials
    user = await auth_service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ============================================
# Allowed Email Domain Management
# ============================================

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
