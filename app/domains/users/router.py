from fastapi import APIRouter, HTTPException, status, Query
from typing import List
from app.domains.users.schema import UserCreate, UserResponse, UserUpdate
from app.domains.users.service import user_service

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """
    사용자 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    """
    users = await user_service.get_users(skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """
    특정 사용자 조회
    
    - **user_id**: 사용자 ID
    """
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):
    """
    새 사용자 생성
    
    - **email**: 이메일 주소
    - **username**: 사용자명 (3-50자)
    - **password**: 비밀번호 (최소 8자)
    - **full_name**: 전체 이름 (선택)
    """
    # 이메일 중복 체크
    existing_user = await user_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = await user_service.create_user(user_data)
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_data: UserUpdate):
    """
    사용자 정보 업데이트
    
    - **user_id**: 사용자 ID
    """
    user = await user_service.update_user(user_id, user_data.model_dump(exclude_unset=True))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int):
    """
    사용자 삭제
    
    - **user_id**: 사용자 ID
    """
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
