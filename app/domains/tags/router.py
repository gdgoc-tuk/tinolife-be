"""
태그 도메인 API 라우터
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.tags.schema import TagListResponse, TagSearchResponse
from app.domains.tags.service import TagService, get_tag_service


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=TagListResponse)
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


@router.get("/search", response_model=TagSearchResponse)
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
        태그 리스트 (사용 빈도 순)
    """
    tags = await service.search_tags(db, q, limit)
    return TagSearchResponse(tags=tags, query=q)
