from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.qna.schema import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    TagListResponse,
    TagSearchResponse,
)
from app.domains.qna.service import (
    CategoryService,
    get_category_service,
    TagService,
    get_tag_service,
)
from app.common.dependencies import get_current_user
from app.domains.users.model import User

router = APIRouter(prefix="/qna", tags=["qna"])


@router.get("/categories", response_model=CategoryListResponse)
async def get_categories(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=100, description="조회할 항목 수"),
    include_inactive: bool = Query(False, description="비활성 카테고리 포함 여부"),
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
):
    """
    카테고리 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    - **include_inactive**: 비활성 카테고리 포함 여부 (기본값: false)
    """
    categories = await service.get_categories(
        db, skip=skip, limit=limit, include_inactive=include_inactive
    )
    total = await service.count_categories(db, include_inactive=include_inactive)

    return CategoryListResponse(categories=categories, total=total)


@router.get("/categories/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
):
    """
    카테고리 상세 조회
    
    - **category_id**: 카테고리 ID
    """
    category = await service.get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="카테고리를 찾을 수 없습니다."
        )
    return category


@router.post(
    "/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
):
    """
    카테고리 생성 (관리자 전용)
    
    - **name**: 카테고리명
    - **display_order**: 표시 순서 (기본값: 0)
    
    TODO: 관리자 권한 체크 추가
    """
    # TODO: 관리자 권한 체크
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    category = await service.create_category(db, category_data)
    return category


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
):
    """
    카테고리 수정 (관리자 전용)
    
    - **name**: 카테고리명 (선택)
    - **display_order**: 표시 순서 (선택)
    - **is_active**: 활성화 상태 (선택)
    
    TODO: 관리자 권한 체크 추가
    """
    # TODO: 관리자 권한 체크
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    category = await service.update_category(db, category_id, category_data)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    service: CategoryService = Depends(get_category_service),
    current_user: User = Depends(get_current_user),
):
    """
    카테고리 삭제 (관리자 전용)
    
    - **category_id**: 카테고리 ID
    
    주의: 사용 중인 카테고리는 삭제할 수 없습니다.
    
    TODO: 관리자 권한 체크 추가
    """
    # TODO: 관리자 권한 체크
    # if not current_user.is_admin:
    #     raise HTTPException(status_code=403, detail="관리자만 접근 가능합니다.")

    await service.delete_category(db, category_id)
    return None


@router.get("/tags", response_model=TagListResponse)
async def get_tags(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=100, description="조회할 항목 수"),
    sort_by: str = Query("usage", pattern="^(usage|recent)$", description="정렬 기준"),
    include_inactive: bool = Query(False, description="비활성 태그 포함 여부"),
    db: Session = Depends(get_db),
    service: TagService = Depends(get_tag_service),
):
    """
    태그 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    - **sort_by**: 정렬 기준 ("usage": 사용 빈도순, "recent": 최신순)
    - **include_inactive**: 비활성 태그 포함 여부
    """
    tags = await service.get_tags(
        db, skip=skip, limit=limit, sort_by=sort_by, include_inactive=include_inactive
    )
    total = await service.count_tags(db, include_inactive=include_inactive)

    return TagListResponse(tags=tags, total=total)


@router.get("/tags/search", response_model=TagSearchResponse)
async def search_tags(
    q: str = Query(..., min_length=1, max_length=50, description="검색 쿼리"),
    limit: int = Query(10, ge=1, le=50, description="최대 결과 수"),
    db: Session = Depends(get_db),
    service: TagService = Depends(get_tag_service),
):
    """
    태그 검색 (자동완성용)
    
    - **q**: 검색 쿼리
    - **limit**: 최대 결과 수 (기본값: 10)
    
    Returns:
        태그명 리스트 (사용 빈도 순)
    """
    tags = await service.search_tags(db, q, limit)
    return TagSearchResponse(tags=tags)
