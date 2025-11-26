"""
QnA 스키마 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


# ========== Category 스키마 ==========

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


# ========== Tag 스키마 ==========

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
    bounty: int = Field(default=0, ge=0, description="바운티 (TINO 토큰)")
    is_anonymous: bool = Field(default=False, description="익명 여부")


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
