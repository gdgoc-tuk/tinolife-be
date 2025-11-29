"""
마이페이지 API 라우터
"""
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.common.dependencies import get_current_user
from app.domains.users.model import User
from app.domains.tino.schema import TinoHistoryResponse
from app.domains.mypage.schema import (
    MypageMainResponse,
    MyQuestionsResponse,
    MyAnswersResponse,
    MyStoriesResponse,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
)
from app.domains.mypage.service import MypageService

router = APIRouter(prefix="/mypage", tags=["mypage"])


def get_mypage_service(db: Session = Depends(get_db)) -> MypageService:
    """마이페이지 서비스 의존성"""
    return MypageService(db)


@router.get("", response_model=MypageMainResponse)
async def get_mypage_main(
    current_user: User = Depends(get_current_user),
    service: MypageService = Depends(get_mypage_service),
):
    """
    마이페이지 메인 조회
    
    프로필 정보, 활동 요약, TINO 잔액을 조회합니다.
    """
    return service.get_mypage_main(current_user)


@router.get("/tino-history", response_model=TinoHistoryResponse)
async def get_tino_history(
    start_date: date | None = Query(None, description="시작일 (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="종료일 (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=50, description="페이지 크기"),
    current_user: User = Depends(get_current_user),
    service: MypageService = Depends(get_mypage_service),
):
    """
    TINO 이력 조회
    
    TINO 토큰 거래 내역을 조회합니다.
    시작일/종료일로 기간 필터링이 가능합니다.
    """
    return service.get_tino_history(
        current_user, start_date, end_date, page, page_size
    )


@router.get("/questions", response_model=MyQuestionsResponse)
async def get_my_questions(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=50, description="페이지 크기"),
    current_user: User = Depends(get_current_user),
    service: MypageService = Depends(get_mypage_service),
):
    """
    내 질문 목록 조회
    
    내가 작성한 질문 목록을 조회합니다.
    """
    return service.get_my_questions(current_user, page, page_size)


@router.get("/answers", response_model=MyAnswersResponse)
async def get_my_answers(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=50, description="페이지 크기"),
    current_user: User = Depends(get_current_user),
    service: MypageService = Depends(get_mypage_service),
):
    """
    내 답변 목록 조회
    
    내가 작성한 답변 목록을 조회합니다.
    """
    return service.get_my_answers(current_user, page, page_size)


@router.get("/stories", response_model=MyStoriesResponse)
async def get_my_stories(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=50, description="페이지 크기"),
    status_filter: str = Query("all", description="상태 필터 (all, recruiting, completed, closed)"),
    current_user: User = Depends(get_current_user),
    service: MypageService = Depends(get_mypage_service),
):
    """
    내 스토리 목록 조회
    
    내가 작성한 티노스토리 목록을 조회합니다.
    status_filter로 모집 상태를 필터링할 수 있습니다.
    """
    return service.get_my_stories(current_user, page, page_size, status_filter)


@router.put("/profile", response_model=ProfileUpdateResponse)
async def update_profile(
    data: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: MypageService = Depends(get_mypage_service),
):
    """
    프로필 수정
    
    닉네임, 학년 등 프로필 정보를 수정합니다.
    """
    return service.update_profile(current_user, data.nickname, data.grade)
