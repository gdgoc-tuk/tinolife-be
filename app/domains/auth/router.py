from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.domains.auth.schema import LoginRequest, LoginResponse
from app.domains.auth.service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
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
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
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
