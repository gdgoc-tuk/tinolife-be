"""
티노스토리 API 라우터
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Query, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.tinostory.schema import (
    StoryCreate,
    StoryUpdate,
    StoryResponse,
    StoryListResponse,
    StoryListItem,
    StoryDetailResponse,
    StoryAuthorResponse,
    StoryTagResponse,
    StoryImageResponse,
    CommentCreate,
    CommentUpdate,
    CommentResponse,
    CommentListResponse,
    CommentAuthorResponse,
    LikeResponse,
    BookmarkResponse,
    BookmarkListResponse,
    ImageUploadResponse,
)
from app.domains.tinostory.service import (
    StoryService,
    get_story_service,
    LikeService,
    get_like_service,
    BookmarkService,
    get_bookmark_service,
    CommentService,
    get_comment_service,
)
from app.common.dependencies import get_current_user
from app.common.image_upload import ImageUploader, get_image_uploader
from app.domains.users.model import User

router = APIRouter(prefix="/tinostory", tags=["tinostory"])


def _build_story_list_item(story, thumbnail_url: str = None) -> StoryListItem:
    """Story 객체를 StoryListItem으로 변환"""
    return StoryListItem(
        id=story.id,
        title=story.title,
        recruitment_type=story.recruitment_type,
        recruitment_status=story.recruitment_status,
        deadline=story.deadline,
        view_count=story.view_count,
        like_count=story.like_count,
        bookmark_count=story.bookmark_count,
        comment_count=story.comment_count,
        created_at=story.created_at,
        author=StoryAuthorResponse(id=story.user.id, nickname=story.user.nickname),
        tags=[StoryTagResponse(id=t.id, name=t.name) for t in story.tags],
        thumbnail_url=story.images[0].image_url if story.images else None,
    )


def _build_story_response(story) -> StoryResponse:
    """Story 객체를 StoryResponse로 변환"""
    return StoryResponse(
        id=story.id,
        title=story.title,
        content=story.content,
        recruitment_type=story.recruitment_type,
        recruitment_status=story.recruitment_status,
        deadline=story.deadline,
        open_chat_link=story.open_chat_link,
        user_id=story.user_id,
        view_count=story.view_count,
        like_count=story.like_count,
        bookmark_count=story.bookmark_count,
        comment_count=story.comment_count,
        is_hidden=story.is_hidden,
        is_deleted=story.is_deleted,
        created_at=story.created_at,
        updated_at=story.updated_at,
        author=StoryAuthorResponse(id=story.user.id, nickname=story.user.nickname),
        tags=[StoryTagResponse(id=t.id, name=t.name) for t in story.tags],
        images=[StoryImageResponse(id=img.id, image_url=img.image_url, display_order=img.display_order) for img in story.images],
    )


@router.get("", response_model=StoryListResponse)
async def get_stories(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(20, ge=1, le=100, description="조회할 항목 수"),
    sort_by: str = Query("recent", pattern="^(recent|deadline|popular)$", description="정렬 기준"),
    status_filter: str = Query("recruiting", pattern="^(recruiting|all)$", description="상태 필터"),
    recruitment_type: str = Query(None, pattern="^(CLUB|STUDY|PROJECT|ACTIVITY|OTHER)$", description="모집 타입 필터"),
    tags: Optional[List[str]] = Query(None, description="태그 필터 (여러 개 가능, OR 조건)"),
    db: Session = Depends(get_db),
    service: StoryService = Depends(get_story_service),
):
    """
    스토리 목록 조회
    
    - **skip**: 건너뛸 항목 수
    - **limit**: 조회할 항목 수 (최대 100)
    - **sort_by**: 정렬 기준 (recent: 최신순, deadline: 마감 임박순, popular: 인기순)
    - **status_filter**: 상태 필터 (recruiting: 모집중만, all: 전체)
    - **recruitment_type**: 모집 타입 필터 (CLUB: 동아리, STUDY: 스터디, PROJECT: 프로젝트, ACTIVITY: 대외활동, OTHER: 기타)
    - **tags**: 태그 필터 (여러 개 가능, OR 조건으로 검색)
    """
    stories, total = await service.get_stories(
        db, skip=skip, limit=limit, sort_by=sort_by, status_filter=status_filter, 
        recruitment_type=recruitment_type, tags=tags
    )
    
    story_items = [_build_story_list_item(story) for story in stories]
    
    return StoryListResponse(stories=story_items, total=total)


@router.get("/{story_id}", response_model=StoryDetailResponse)
async def get_story(
    story_id: int,
    db: Session = Depends(get_db),
    service: StoryService = Depends(get_story_service),
    current_user: User = Depends(get_current_user),
):
    """
    스토리 상세 조회
    
    - **story_id**: 스토리 ID
    """
    story = await service.get_story_by_id(db, story_id)
    if not story:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="스토리를 찾을 수 없습니다."
        )
    
    # 조회수 증가
    await service.increment_view_count(db, story_id)
    
    # 좋아요/북마크 여부 확인
    from app.domains.tinostory.service import get_like_service, get_bookmark_service
    like_service = get_like_service()
    bookmark_service = get_bookmark_service()
    
    is_liked = await like_service.is_liked(db, story_id, current_user.id)
    is_bookmarked = await bookmark_service.is_bookmarked(db, story_id, current_user.id)
    
    response = _build_story_response(story)
    return StoryDetailResponse(
        **response.model_dump(),
        is_liked=is_liked,
        is_bookmarked=is_bookmarked
    )


@router.post("", response_model=StoryResponse, status_code=status.HTTP_201_CREATED)
async def create_story(
    story_data: StoryCreate,
    db: Session = Depends(get_db),
    service: StoryService = Depends(get_story_service),
    current_user: User = Depends(get_current_user),
):
    """
    스토리 생성
    
    - **title**: 제목
    - **content**: 본문
    - **recruitment_type**: 모집 타입 (CLUB, STUDY, PROJECT, ACTIVITY, OTHER)
    - **deadline**: 모집 마감일
    - **open_chat_link**: 오픈채팅 링크
    - **tag_names**: 태그 리스트 (선택)
    """
    story = await service.create_story(db, story_data, current_user.id)
    return _build_story_response(story)


@router.put("/{story_id}", response_model=StoryResponse)
async def update_story(
    story_id: int,
    story_data: StoryUpdate,
    db: Session = Depends(get_db),
    service: StoryService = Depends(get_story_service),
    current_user: User = Depends(get_current_user),
):
    """
    스토리 수정
    
    - **story_id**: 스토리 ID
    - 수정할 필드만 전달
    """
    story = await service.update_story(db, story_id, story_data, current_user.id)
    return _build_story_response(story)


@router.delete("/{story_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_story(
    story_id: int,
    db: Session = Depends(get_db),
    service: StoryService = Depends(get_story_service),
    current_user: User = Depends(get_current_user),
):
    """
    스토리 삭제
    
    - **story_id**: 스토리 ID
    """
    await service.delete_story(db, story_id, current_user.id)
    return None


@router.post("/{story_id}/like", response_model=LikeResponse)
async def toggle_like(
    story_id: int,
    db: Session = Depends(get_db),
    service: LikeService = Depends(get_like_service),
    current_user: User = Depends(get_current_user),
):
    """
    스토리 좋아요 토글
    
    - **story_id**: 스토리 ID
    - 좋아요가 없으면 추가, 있으면 취소
    """
    is_liked, like_count = await service.toggle_like(db, story_id, current_user.id)
    return LikeResponse(is_liked=is_liked, like_count=like_count)


@router.post("/{story_id}/bookmark", response_model=BookmarkResponse)
async def toggle_bookmark(
    story_id: int,
    db: Session = Depends(get_db),
    service: BookmarkService = Depends(get_bookmark_service),
    current_user: User = Depends(get_current_user),
):
    """
    스토리 북마크 토글
    
    - **story_id**: 스토리 ID
    - 북마크가 없으면 추가, 있으면 취소
    """
    is_bookmarked, bookmark_count = await service.toggle_bookmark(db, story_id, current_user.id)
    return BookmarkResponse(is_bookmarked=is_bookmarked, bookmark_count=bookmark_count)


@router.get("/bookmarks/me", response_model=BookmarkListResponse)
async def get_my_bookmarks(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(20, ge=1, le=100, description="조회할 항목 수"),
    db: Session = Depends(get_db),
    service: BookmarkService = Depends(get_bookmark_service),
    current_user: User = Depends(get_current_user),
):
    """
    내 북마크 목록 조회
    """
    stories, total = await service.get_bookmarked_stories(db, current_user.id, skip, limit)
    story_items = [_build_story_list_item(story) for story in stories]
    return BookmarkListResponse(stories=story_items, total=total)


@router.get("/{story_id}/comments", response_model=CommentListResponse)
async def get_comments(
    story_id: int,
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(50, ge=1, le=100, description="조회할 항목 수"),
    db: Session = Depends(get_db),
    service: CommentService = Depends(get_comment_service),
):
    """
    스토리 댓글 목록 조회
    
    - **story_id**: 스토리 ID
    """
    comments, total = await service.get_comments(db, story_id, skip, limit)
    
    comment_responses = [
        CommentResponse(
            id=c.id,
            story_id=c.story_id,
            content=c.content,
            is_hidden=c.is_hidden,
            is_deleted=c.is_deleted,
            created_at=c.created_at,
            updated_at=c.updated_at,
            author=CommentAuthorResponse(id=c.user.id, nickname=c.user.nickname)
        )
        for c in comments
    ]
    
    return CommentListResponse(comments=comment_responses, total=total)


@router.post("/{story_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def create_comment(
    story_id: int,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user),
):
    """
    스토리 댓글 작성
    
    - **story_id**: 스토리 ID
    - **content**: 댓글 내용
    """
    comment = await service.create_comment(db, story_id, current_user.id, comment_data.content)
    
    # user 정보 로드
    from sqlalchemy.orm import joinedload
    comment = db.query(type(comment)).options(
        joinedload(type(comment).user)
    ).filter(type(comment).id == comment.id).first()
    
    return CommentResponse(
        id=comment.id,
        story_id=comment.story_id,
        content=comment.content,
        is_hidden=comment.is_hidden,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=CommentAuthorResponse(id=comment.user.id, nickname=comment.user.nickname)
    )


@router.put("/comments/{comment_id}", response_model=CommentResponse)
async def update_comment(
    comment_id: int,
    comment_data: CommentUpdate,
    db: Session = Depends(get_db),
    service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user),
):
    """
    댓글 수정
    
    - **comment_id**: 댓글 ID
    - **content**: 수정할 내용
    """
    comment = await service.update_comment(db, comment_id, current_user.id, comment_data.content)
    
    return CommentResponse(
        id=comment.id,
        story_id=comment.story_id,
        content=comment.content,
        is_hidden=comment.is_hidden,
        is_deleted=comment.is_deleted,
        created_at=comment.created_at,
        updated_at=comment.updated_at,
        author=CommentAuthorResponse(id=comment.user.id, nickname=comment.user.nickname)
    )


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    service: CommentService = Depends(get_comment_service),
    current_user: User = Depends(get_current_user),
):
    """
    댓글 삭제
    
    - **comment_id**: 댓글 ID
    """
    await service.delete_comment(db, comment_id, current_user.id)
    return None


@router.post("/images/upload", response_model=ImageUploadResponse)
async def upload_image(
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
    current_user: User = Depends(get_current_user),
    uploader: ImageUploader = Depends(get_image_uploader),
):
    """
    이미지 업로드
    
    스토리 본문에 삽입할 이미지를 업로드합니다.
    
    - **file**: 이미지 파일 (JPEG, PNG, GIF, WebP)
    - 최대 파일 크기: 5MB
    
    업로드 후 반환된 image_url을 본문에 삽입하여 사용합니다.
    """
    # prefix 설정
    prefix = "tinostory/images"
    
    # 이미지 업로드
    image_url, image_key, file_size, mime_type = await uploader.upload(file, prefix)
    
    return ImageUploadResponse(
        image_url=image_url,
        image_key=image_key,
        file_size=file_size,
        mime_type=mime_type,
        message="이미지가 성공적으로 업로드되었습니다"
    )
