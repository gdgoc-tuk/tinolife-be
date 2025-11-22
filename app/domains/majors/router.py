from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.domains.majors.schema import MajorCreate, MajorUpdate, MajorResponse
from app.domains.majors.service import MajorService, get_major_service

router = APIRouter(prefix="/majors", tags=["majors"])


@router.get("/", response_model=List[MajorResponse])
async def get_majors(
    active_only: bool = Query(True, description="활성화된 전공만 조회"),
    db: Session = Depends(get_db),
    service: MajorService = Depends(get_major_service),
):
    """
    전공 전체 목록 조회

    - **active_only**: 활성화된 전공만 조회 여부
    """
    majors = await service.get_majors(db, active_only=active_only)
    return majors


@router.get("/{major_id}", response_model=MajorResponse)
async def get_major(
    major_id: int,
    db: Session = Depends(get_db),
    service: MajorService = Depends(get_major_service),
):
    """
    특정 전공 조회

    - **major_id**: 전공 ID
    """
    major = await service.get_major_by_id(db, major_id)
    if not major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Major not found"
        )
    return major


@router.post("/", response_model=MajorResponse, status_code=status.HTTP_201_CREATED)
async def create_major(
    major_data: MajorCreate,
    db: Session = Depends(get_db),
    service: MajorService = Depends(get_major_service),
):
    """
    새 전공 생성

    - **name**: 전공명 (필수)
    - **code**: 전공 코드 (선택)
    """
    # 중복 체크
    existing_major = await service.get_major_by_name(db, major_data.name)
    if existing_major:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Major with this name already exists",
        )

    major = await service.create_major(db, major_data)
    return major


@router.put("/{major_id}", response_model=MajorResponse)
async def update_major(
    major_id: int,
    major_data: MajorUpdate,
    db: Session = Depends(get_db),
    service: MajorService = Depends(get_major_service),
):
    """
    전공 정보 업데이트

    - **major_id**: 전공 ID
    """
    major = await service.update_major(db, major_id, major_data)
    if not major:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Major not found"
        )
    return major


@router.delete("/{major_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_major(
    major_id: int,
    db: Session = Depends(get_db),
    service: MajorService = Depends(get_major_service),
):
    """
    전공 삭제 (소프트 삭제)

    - **major_id**: 전공 ID
    """
    success = await service.delete_major(db, major_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Major not found"
        )
