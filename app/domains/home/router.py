"""
홈 화면 API 라우터
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.dependencies import get_current_user
from app.domains.users.model import User
from app.domains.home.schema import (
    FeaturedQuestionsResponse,
    RecentQuestionsResponse,
    RecommendedStoriesResponse,
)
from app.domains.home.service import HomeService, get_home_service

router = APIRouter(prefix="/home", tags=["home"])


@router.get("/featured-questions", response_model=FeaturedQuestionsResponse)
async def get_featured_questions(
    limit: int = Query(5, ge=1, le=10, description="최대 개수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: HomeService = Depends(get_home_service),
):
    """
    주목 질문 목록 조회
    
    나와 관련된 트렌딩/인기 QnA 질문을 개인화하여 반환합니다.
    
    **개인화 기준:**
    - 전공 일치
    - 학년 관련 키워드 (1학년, 졸업, 취준 등)
    - 관심사 태그 매칭
    - 트렌딩 (24시간 내 추천 급증)
    
    각 질문에는 "왜 이 질문이 보이나요?" (reason) 필드가 포함됩니다.
    """
    return await service.get_featured_questions(db, current_user, limit)


@router.get("/recent-questions", response_model=RecentQuestionsResponse)
async def get_recent_questions(
    limit: int = Query(10, ge=1, le=20, description="최대 개수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: HomeService = Depends(get_home_service),
):
    """
    최신 질문 목록 조회
    
    전체 커뮤니티에서 새로 올라온 질문을 최신순으로 반환합니다.
    """
    return await service.get_recent_questions(db, limit)


@router.get("/recommended-stories", response_model=RecommendedStoriesResponse)
async def get_recommended_stories(
    limit: int = Query(5, ge=1, le=10, description="최대 개수"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service: HomeService = Depends(get_home_service),
):
    """
    추천 스토리 목록 조회
    
    나와 관련된 모집글(티노스토리)을 개인화하여 반환합니다.
    
    **개인화 기준:**
    - 전공 일치
    - 관심사 태그 매칭
    - 마감 임박도
    
    모집중(RECRUITING) 상태인 스토리만 반환됩니다.
    각 스토리에는 "왜 이 스토리가 보이나요?" (reason) 필드가 포함됩니다.
    """
    return await service.get_recommended_stories(db, current_user, limit)
