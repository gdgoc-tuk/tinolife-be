"""
태그 도메인 스키마
"""
from pydantic import BaseModel, ConfigDict


class TagBase(BaseModel):
    """태그 기본 스키마"""
    name: str


class TagResponse(TagBase):
    """태그 응답 스키마"""
    id: int
    usage_count: int
    is_active: bool
    is_official: bool
    
    model_config = ConfigDict(from_attributes=True)


class TagListResponse(BaseModel):
    """태그 목록 응답 스키마"""
    tags: list[TagResponse]
    total: int


class TagSearchResponse(BaseModel):
    """태그 검색 응답 스키마"""
    tags: list[TagResponse]
    query: str
