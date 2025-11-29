"""
티노스토리 스키마 정의
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional
from app.domains.tinostory.model import RecruitmentType, RecruitmentStatus


class StoryBase(BaseModel):
    """스토리 기본 스키마"""
    title: str = Field(..., min_length=1, max_length=200, description="제목")
    content: str = Field(..., min_length=1, description="본문")
    recruitment_type: RecruitmentType = Field(..., description="모집 타입")
    deadline: datetime = Field(..., description="모집 마감일")
    open_chat_link: str = Field(..., min_length=1, max_length=500, description="오픈채팅 링크")


class StoryCreate(StoryBase):
    """스토리 생성 스키마"""
    tag_names: list[str] = Field(default=[], max_length=10, description="태그명 리스트")


class StoryUpdate(BaseModel):
    """스토리 수정 스키마"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="제목")
    content: Optional[str] = Field(None, min_length=1, description="본문")
    recruitment_type: Optional[RecruitmentType] = Field(None, description="모집 타입")
    recruitment_status: Optional[RecruitmentStatus] = Field(None, description="모집 상태")
    deadline: Optional[datetime] = Field(None, description="모집 마감일")
    open_chat_link: Optional[str] = Field(None, min_length=1, max_length=500, description="오픈채팅 링크")
    tag_names: Optional[list[str]] = Field(None, max_length=10, description="태그명 리스트")


class StoryAuthorResponse(BaseModel):
    """스토리 작성자 응답 스키마"""
    id: int
    nickname: str
    
    model_config = ConfigDict(from_attributes=True)


class StoryTagResponse(BaseModel):
    """스토리 태그 응답 스키마"""
    id: int
    name: str
    
    model_config = ConfigDict(from_attributes=True)


class StoryImageResponse(BaseModel):
    """스토리 이미지 응답 스키마"""
    id: int
    image_url: str
    display_order: int
    
    model_config = ConfigDict(from_attributes=True)


class StoryResponse(StoryBase):
    """스토리 응답 스키마"""
    id: int
    user_id: int
    recruitment_status: RecruitmentStatus
    view_count: int
    like_count: int
    bookmark_count: int
    comment_count: int
    is_hidden: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    author: StoryAuthorResponse
    tags: list[StoryTagResponse]
    images: list[StoryImageResponse]
    
    model_config = ConfigDict(from_attributes=True)


class StoryListItem(BaseModel):
    """스토리 목록 아이템 스키마 (요약)"""
    id: int
    title: str
    recruitment_type: RecruitmentType
    recruitment_status: RecruitmentStatus
    deadline: datetime
    view_count: int
    like_count: int
    bookmark_count: int
    comment_count: int
    created_at: datetime
    
    author: StoryAuthorResponse
    tags: list[StoryTagResponse]
    thumbnail_url: Optional[str] = None  # 대표 이미지
    
    model_config = ConfigDict(from_attributes=True)


class StoryListResponse(BaseModel):
    """스토리 목록 응답 스키마"""
    stories: list[StoryListItem]
    total: int


class StoryDetailResponse(StoryResponse):
    """스토리 상세 응답 스키마 (사용자 상호작용 정보 포함)"""
    is_liked: bool = False      # 현재 사용자 좋아요 여부
    is_bookmarked: bool = False # 현재 사용자 북마크 여부


class CommentAuthorResponse(BaseModel):
    """댓글 작성자 응답 스키마"""
    id: int
    nickname: str
    
    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    """댓글 생성 스키마"""
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용")


class CommentUpdate(BaseModel):
    """댓글 수정 스키마"""
    content: str = Field(..., min_length=1, max_length=500, description="댓글 내용")


class CommentResponse(BaseModel):
    """댓글 응답 스키마"""
    id: int
    story_id: int
    content: str
    is_hidden: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    
    author: CommentAuthorResponse
    
    model_config = ConfigDict(from_attributes=True)


class CommentListResponse(BaseModel):
    """댓글 목록 응답 스키마"""
    comments: list[CommentResponse]
    total: int


class LikeResponse(BaseModel):
    """좋아요 응답 스키마"""
    is_liked: bool
    like_count: int


class BookmarkResponse(BaseModel):
    """북마크 응답 스키마"""
    is_bookmarked: bool
    bookmark_count: int


class BookmarkListResponse(BaseModel):
    """북마크 목록 응답 스키마"""
    stories: list[StoryListItem]
    total: int
