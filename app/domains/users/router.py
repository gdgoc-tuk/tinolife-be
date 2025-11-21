from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import List
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domains.users.schema import (
    UserCreate, UserResponse, UserUpdate,
    NicknameCheckResponse
)
from app.domains.users.service import get_user_service, UserService
from app.domains.interests.schema import UserInterestsRequest, UserInterestsResponse, InterestResponse
from app.common.dependencies import get_current_user
from app.domains.users.model import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/check-nickname", response_model=NicknameCheckResponse)
async def check_nickname(
    nickname: str = Query(..., min_length=2, max_length=20, description="확인할 닉네임"),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    닉네임 중복 확인
    
    - **nickname**: 확인할 닉네임 (2-20자)
    
    Returns:
        - available: 사용 가능 여부 (true/false)
        - message: 결과 메시지
    """
    # 중복 체크
    is_available = user_service.check_nickname_availability(db, nickname)
    
    if is_available:
        return NicknameCheckResponse(
            available=True,
            message="사용 가능한 닉네임입니다."
        )
    else:
        return NicknameCheckResponse(
            available=False,
            message="이미 사용 중인 닉네임입니다."
        )


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    """
    users = user_service.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    특정 사용자 조회
    
    - **user_id**: 사용자 ID
    """
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    새 사용자 생성
    
    - **email**: 이메일 주소
    - **username**: 사용자명 (3-50자)
    - **password**: 비밀번호 (최소 8자)
    - **full_name**: 전체 이름 (선택)
    """
    # 이메일 중복 체크
    existing_user = user_service.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = user_service.create_user(db, user_data)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 정보 업데이트
    
    - **user_id**: 사용자 ID
    """
    user = user_service.update_user(db, user_id, user_data.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    사용자 삭제
    
    - **user_id**: 사용자 ID
    """
    success = user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )


@router.get("/me/interests", response_model=List[InterestResponse])
async def get_my_interests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 관심사 목록 조회
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    
    Returns:
        현재 사용자의 관심사 목록
    """
    # user.interests는 SQLAlchemy relationship으로 자동 로드됨
    return [
        InterestResponse(
            id=interest.id,
            name=interest.name,
            is_active=interest.is_active,
            created_at=interest.created_at
        )
        for interest in current_user.interests
    ]


@router.put("/me/interests", response_model=UserInterestsResponse)
async def update_my_interests(
    request: UserInterestsRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service)
):
    """
    현재 사용자의 관심사 업데이트
    
    기존 관심사를 모두 제거하고 새로운 관심사로 대체합니다.
    
    Authorization 헤더에 Bearer 토큰이 필요합니다.
    
    - **interest_ids**: 관심사 ID 목록
    
    Returns:
        업데이트된 관심사 목록
        
    Raises:
        - 400: 존재하지 않는 관심사 ID
    """
    from app.common.exceptions import BadRequestException
    
    try:
        # 기존 관심사 제거 및 새 관심사 추가
        user_service.update_user_interests(db, current_user.id, request.interest_ids)
        
        # 업데이트된 사용자 정보 다시 조회
        db.refresh(current_user)
        
        return UserInterestsResponse(
            user_id=current_user.id,
            interests=[
                InterestResponse(
                    id=interest.id,
                    name=interest.name,
                    is_active=interest.is_active,
                    created_at=interest.created_at
                )
                for interest in current_user.interests
            ],
            message="관심사가 업데이트되었습니다."
        )
        
    except BadRequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e.detail)
        )
