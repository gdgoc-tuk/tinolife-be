"""
홈 화면 API 스키마
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.domains.qna.schema import CategoryResponse, TagResponse
from app.domains.majors.schema import MajorResponse


class FeaturedQuestionItem(BaseModel):
    """주목 질문 아이템"""
    id: int
    title: str
    content_preview: str  # 본문 앞 100자
    category: CategoryResponse
    major: Optional[MajorResponse] = None
    tags: list[TagResponse]
    bounty: int
    interest_count: int
    answer_count: int
    view_count: int
    reason: str  # "왜 이 질문이 보이나요?"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FeaturedQuestionsResponse(BaseModel):
    """주목 질문 목록 응답"""
    questions: list[FeaturedQuestionItem]
    total: int


class RecentQuestionItem(BaseModel):
    """최신 질문 아이템"""
    id: int
    title: str
    content_preview: str
    category: CategoryResponse
    major: Optional[MajorResponse] = None
    tags: list[TagResponse]
    bounty: int
    interest_count: int
    answer_count: int
    view_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecentQuestionsResponse(BaseModel):
    """최신 질문 목록 응답"""
    questions: list[RecentQuestionItem]
    total: int


class RecommendedStoryItem(BaseModel):
    """추천 스토리 아이템"""
    id: int
    title: str
    recruitment_type: str
    recruitment_status: str
    thumbnail_url: Optional[str] = None
    tags: list[TagResponse]
    deadline: Optional[datetime] = None
    days_until_deadline: Optional[int] = None  # D-Day 계산
    like_count: int
    author_nickname: str
    reason: str  # "왜 이 스토리가 보이나요?"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendedStoriesResponse(BaseModel):
    """추천 스토리 목록 응답"""
    stories: list[RecommendedStoryItem]
    total: int
