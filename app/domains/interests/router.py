from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from math import ceil

from app.core.database import get_db
from app.domains.interests.schema import (
    InterestCreate, 
    InterestUpdate, 
    InterestResponse,
    PaginatedInterestResponse
)
from app.domains.interests.service import InterestService, get_interest_service

router = APIRouter(prefix="/interests", tags=["interests"])


@router.get("/", response_model=PaginatedInterestResponse)
async def get_interests(
    page: int = Query(1, ge=1, description="페이지 번호 (1부터 시작)"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기 (최대 100)"),
    active_only: bool = Query(True, description="활성화된 관심사만 조회"),
    db: Session = Depends(get_db),
    service: InterestService = Depends(get_interest_service)
):
    """
    관심사 목록 조회 (페이지네이션)
    
    - **page**: 페이지 번호 (1부터 시작)
    - **size**: 페이지 크기 (최대 100)
    - **active_only**: 활성화된 관심사만 조회 여부
    """
    skip = (page - 1) * size
    interests = await service.get_interests(db, skip=skip, limit=size, active_only=active_only)
    total = await service.get_interest_count(db, active_only=active_only)
    total_pages = ceil(total / size) if total > 0 else 1
    
    return PaginatedInterestResponse(
        items=interests,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )


@router.get("/{interest_id}", response_model=InterestResponse)
async def get_interest(
    interest_id: int,
    db: Session = Depends(get_db),
    service: InterestService = Depends(get_interest_service)
):
    """
    특정 관심사 조회
    
    - **interest_id**: 관심사 ID
    """
    interest = await service.get_interest_by_id(db, interest_id)
    if not interest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interest not found"
        )
    return interest


@router.post("/", response_model=InterestResponse, status_code=status.HTTP_201_CREATED)
async def create_interest(
    interest_data: InterestCreate,
    db: Session = Depends(get_db),
    service: InterestService = Depends(get_interest_service)
):
    """
    새 관심사 생성
    
    - **name**: 관심사명 (필수)
    """
    # 중복 체크
    existing_interest = await service.get_interest_by_name(db, interest_data.name)
    if existing_interest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Interest with this name already exists"
        )
    
    interest = await service.create_interest(db, interest_data)
    return interest


@router.put("/{interest_id}", response_model=InterestResponse)
async def update_interest(
    interest_id: int,
    interest_data: InterestUpdate,
    db: Session = Depends(get_db),
    service: InterestService = Depends(get_interest_service)
):
    """
    관심사 정보 업데이트
    
    - **interest_id**: 관심사 ID
    """
    interest = await service.update_interest(db, interest_id, interest_data)
    if not interest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interest not found"
        )
    return interest


@router.delete("/{interest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_interest(
    interest_id: int,
    db: Session = Depends(get_db),
    service: InterestService = Depends(get_interest_service)
):
    """
    관심사 삭제 (소프트 삭제)
    
    - **interest_id**: 관심사 ID
    """
    success = await service.delete_interest(db, interest_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interest not found"
        )
