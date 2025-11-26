"""
QnA 스키마 정의
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional


class CategoryBase(BaseModel):
    """카테고리 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=50, description="카테고리명")
    display_order: int = Field(default=0, ge=0, description="표시 순서")


class CategoryCreate(CategoryBase):
    """카테고리 생성 스키마"""
    pass


class CategoryUpdate(BaseModel):
    """카테고리 수정 스키마"""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="카테고리명")
    display_order: Optional[int] = Field(None, ge=0, description="표시 순서")
    is_active: Optional[bool] = Field(None, description="활성화 상태")


class CategoryResponse(CategoryBase):
    """카테고리 응답 스키마"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    """카테고리 목록 응답 스키마"""
    categories: list[CategoryResponse]
    total: int


class TagBase(BaseModel):
    """태그 기본 스키마"""
    name: str = Field(..., min_length=1, max_length=50, description="태그명")


class TagResponse(TagBase):
    """태그 응답 스키마"""
    id: int
    usage_count: int
    is_active: bool
    is_official: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TagListResponse(BaseModel):
    """태그 목록 응답 스키마"""
    tags: list[TagResponse]
    total: int


class TagSearchResponse(BaseModel):
    """태그 검색 응답 스키마"""
    tags: list[TagResponse]


class QuestionBase(BaseModel):
    """질문 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="제목")
    content: str = Field(..., min_length=1, description="본문")
    category_id: int = Field(..., gt=0, description="카테고리 ID")
    major_id: Optional[int] = Field(None, gt=0, description="전공 ID (null=전공무관)")
    bounty: int = Field(default=0, ge=0, le=100, description="바운티 (TINO 토큰, 0 또는 5~100)")
    is_anonymous: bool = Field(default=False, description="익명 여부")
    
    @field_validator('bounty')
    @classmethod
    def validate_bounty(cls, v: int) -> int:
        """바운티 정책: 0(무료) 또는 최소 5 ~ 최대 100"""
        if v != 0 and (v < 5 or v > 100):
            raise ValueError('바운티는 0(무료) 또는 5~100 TINO 사이여야 합니다')
        return v


class QuestionCreate(QuestionBase):
    """질문 생성 스키마"""
    tag_names: list[str] = Field(default=[], max_length=10, description="태그명 리스트")


class QuestionUpdate(BaseModel):
    """질문 수정 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="제목")
    content: Optional[str] = Field(None, min_length=1, description="본문")
    category_id: Optional[int] = Field(None, gt=0, description="카테고리 ID")
    major_id: Optional[int] = Field(None, gt=0, description="전공 ID")
    is_anonymous: Optional[bool] = Field(None, description="익명 여부")
    tag_names: Optional[list[str]] = Field(None, max_length=10, description="태그명 리스트")
    bounty: Optional[int] = Field(None, ge=0, le=100, description="바운티 증가 (상향 조정만 가능)")
    
    @field_validator('bounty')
    @classmethod
    def validate_bounty(cls, v: Optional[int]) -> Optional[int]:
        """바운티 정책: 0(무료) 또는 최소 5 ~ 최대 100"""
        if v is not None and v != 0 and (v < 5 or v > 100):
            raise ValueError('바운티는 0(무료) 또는 5~100 TINO 사이여야 합니다')
        return v


class QuestionAuthorResponse(BaseModel):
    """질문 작성자 응답 스키마"""
    id: int
    nickname: str
    is_anonymous: bool
    
    model_config = ConfigDict(from_attributes=True)


class QuestionMajorResponse(BaseModel):
    """질문 전공 응답 스키마"""
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class QuestionResponse(QuestionBase):
    """질문 응답 스키마"""
    id: int
    user_id: int
    view_count: int
    interest_count: int
    answer_count: int
    is_hidden: bool
    is_deleted: bool
    accepted_answer_id: Optional[int]
    accepted_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    category: CategoryResponse
    major: Optional[QuestionMajorResponse]
    tags: list[TagResponse]
    
    model_config = ConfigDict(from_attributes=True)


class QuestionListItem(BaseModel):
    """질문 목록 아이템 스키마"""
    id: int
    title: str
    category: CategoryResponse
    major: Optional[QuestionMajorResponse]
    tags: list[TagResponse]
    bounty: int
    view_count: int
    interest_count: int
    answer_count: int
    is_anonymous: bool
    accepted_answer_id: Optional[int]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class QuestionListResponse(BaseModel):
    """질문 목록 응답 스키마"""
    questions: list[QuestionListItem]
    total: int
    page: int
    page_size: int


class AnswerCreate(BaseModel):
    """답변 생성 스키마"""
    content: str = Field(..., min_length=1, description="답변 내용")
    is_anonymous: bool = Field(default=False, description="익명 여부")


class AnswerUpdate(BaseModel):
    """답변 수정 스키마"""
    content: Optional[str] = Field(None, min_length=1, description="답변 내용")
    is_anonymous: Optional[bool] = Field(None, description="익명 여부")


class AnswerAuthorResponse(BaseModel):
    """답변 작성자 응답 스키마"""
    id: int
    nickname: str
    
    model_config = ConfigDict(from_attributes=True)


class AnswerResponse(BaseModel):
    """답변 응답 스키마"""
    id: int
    question_id: int
    user_id: int
    content: str
    is_anonymous: bool
    like_count: int
    dislike_count: int
    is_accepted: bool
    is_hidden: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AnswerListResponse(BaseModel):
    """답변 목록 응답 스키마"""
    answers: list[AnswerResponse]
    total: int


class AnswerVoteRequest(BaseModel):
    """답변 투표 요청 스키마"""
    vote_type: str = Field(..., description="투표 타입 (like/dislike)")
    
    @field_validator('vote_type')
    @classmethod
    def validate_vote_type(cls, v: str) -> str:
        if v not in ['like', 'dislike']:
            raise ValueError("투표 타입은 'like' 또는 'dislike'여야 합니다")
        return v


class AnswerCommentCreate(BaseModel):
    """답변 댓글 생성 스키마"""
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용")


class AnswerCommentUpdate(BaseModel):
    """답변 댓글 수정 스키마"""
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용")


class AnswerCommentResponse(BaseModel):
    """답변 댓글 응답 스키마"""
    id: int
    answer_id: int
    user_id: int
    content: str
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AnswerCommentListResponse(BaseModel):
    """답변 댓글 목록 응답 스키마"""
    comments: list[AnswerCommentResponse]
    total: int


class InterestResponse(BaseModel):
    """관심 표시 응답 스키마"""
    question_id: int
    is_interested: bool
    interest_count: int
    message: str


class BookmarkResponse(BaseModel):
    """북마크 응답 스키마"""
    question_id: int
    is_bookmarked: bool
    message: str


class BookmarkListItem(BaseModel):
    """북마크 목록 아이템 스키마"""
    id: int
    question_id: int
    question_title: str
    question_bounty: int
    question_answer_count: int
    question_is_accepted: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class BookmarkListResponse(BaseModel):
    """북마크 목록 응답 스키마"""
    bookmarks: list[BookmarkListItem]
    total: int
    page: int
    page_size: int
