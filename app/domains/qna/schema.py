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
