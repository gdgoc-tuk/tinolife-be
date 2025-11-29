"""
마이페이지 스키마 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional
from app.domains.majors.schema import MajorResponse
from app.domains.qna.schema import CategoryResponse
from app.domains.tags.schema import TagResponse
from app.domains.tinostory.model import RecruitmentType, RecruitmentStatus


class ProfileResponse(BaseModel):
    """프로필 응답 스키마"""
    id: int
    nickname: str
    email: str
    grade: Optional[int] = None
    major: Optional[MajorResponse] = None
    student_id: str
    profile_image_url: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ActivitySummaryResponse(BaseModel):
    """활동 요약 응답 스키마"""
    question_count: int = Field(..., description="내가 올린 질문 수")
    answer_count: int = Field(..., description="내가 작성한 답변 수")
    accepted_answer_count: int = Field(..., description="채택된 답변 수")
    story_count: int = Field(..., description="내가 올린 스토리 수")


class TinoSummaryResponse(BaseModel):
    """TINO 요약 응답 스키마"""
    balance: int = Field(..., description="현재 보유 TINO")


class MypageMainResponse(BaseModel):
    """마이페이지 메인 응답 스키마"""
    profile: ProfileResponse
    activity_summary: ActivitySummaryResponse
    tino: TinoSummaryResponse


class MyQuestionItem(BaseModel):
    """내 질문 아이템 스키마"""
    id: int
    title: str
    category: CategoryResponse
    major: Optional[MajorResponse] = None
    tags: list[TagResponse]
    bounty: int
    interest_count: int
    answer_count: int
    is_accepted: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MyQuestionsResponse(BaseModel):
    """내 질문 목록 응답 스키마"""
    questions: list[MyQuestionItem]
    total: int
    page: int
    page_size: int


class MyAnswerItem(BaseModel):
    """내 답변 아이템 스키마"""
    id: int
    question_id: int
    question_title: str
    content_preview: str
    like_count: int
    is_accepted: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MyAnswersResponse(BaseModel):
    """내 답변 목록 응답 스키마"""
    answers: list[MyAnswerItem]
    total: int
    page: int
    page_size: int


class MyStoryItem(BaseModel):
    """내 스토리 아이템 스키마"""
    id: int
    title: str
    recruitment_type: RecruitmentType
    recruitment_status: RecruitmentStatus
    deadline: Optional[datetime] = None
    days_until_deadline: Optional[int] = None
    like_count: int
    comment_count: int
    bookmark_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class MyStoriesResponse(BaseModel):
    """내 스토리 목록 응답 스키마"""
    stories: list[MyStoryItem]
    total: int
    page: int
    page_size: int


class ProfileUpdateRequest(BaseModel):
    """프로필 수정 요청 스키마"""
    nickname: Optional[str] = Field(None, min_length=1, max_length=20, description="닉네임")
    grade: Optional[int] = Field(None, ge=1, le=4, description="학년 (1-4)")


class ProfileUpdateResponse(BaseModel):
    """프로필 수정 응답 스키마"""
    id: int
    nickname: str
    email: str
    grade: Optional[int] = None
    major: Optional[MajorResponse] = None
    student_id: str
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
