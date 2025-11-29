"""
티노스토리 서비스 로직
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime, timezone

from app.domains.tinostory.model import (
    Story, StoryImage, StoryLike, StoryBookmark, StoryComment, StoryReport,
    RecruitmentStatus, story_tags
)
from app.domains.tinostory.schema import StoryCreate, StoryUpdate
from app.domains.qna.model import Tag
from app.common.exceptions import BadRequestException, NotFoundException, ForbiddenException


class StoryService:
    """스토리 비즈니스 로직 서비스"""

    async def get_story_by_id(
        self, 
        db: Session, 
        story_id: int,
        include_deleted: bool = False
    ) -> Optional[Story]:
        """ID로 스토리 조회"""
        query = db.query(Story).options(
            joinedload(Story.user),
            joinedload(Story.tags),
            joinedload(Story.images),
        ).filter(Story.id == story_id)
        
        if not include_deleted:
            query = query.filter(Story.is_deleted == False)
        
        return query.first()

    async def create_story(
        self,
        db: Session,
        story_data: StoryCreate,
        user_id: int
    ) -> Story:
        """스토리 생성"""
        # 스토리 생성
        story = Story(
            user_id=user_id,
            title=story_data.title,
            content=story_data.content,
            recruitment_type=story_data.recruitment_type,
            deadline=story_data.deadline,
            open_chat_link=story_data.open_chat_link,
        )
        
        db.add(story)
        db.flush()  # ID 생성을 위해 flush
        
        # 태그 처리
        if story_data.tag_names:
            await self._process_tags(db, story, story_data.tag_names)
        
        db.commit()
        db.refresh(story)
        
        return await self.get_story_by_id(db, story.id)

    async def update_story(
        self,
        db: Session,
        story_id: int,
        story_data: StoryUpdate,
        user_id: int
    ) -> Story:
        """스토리 수정"""
        story = await self.get_story_by_id(db, story_id)
        if not story:
            raise NotFoundException("스토리를 찾을 수 없습니다.")
        
        # 작성자 확인
        if story.user_id != user_id:
            raise ForbiddenException("본인의 스토리만 수정할 수 있습니다.")
        
        # 필드 업데이트
        update_data = story_data.model_dump(exclude_unset=True)
        tag_names = update_data.pop("tag_names", None)
        
        for key, value in update_data.items():
            setattr(story, key, value)
        
        # 태그 업데이트
        if tag_names is not None:
            story.tags.clear()
            await self._process_tags(db, story, tag_names)
        
        db.commit()
        db.refresh(story)
        
        return await self.get_story_by_id(db, story.id)

    async def delete_story(
        self,
        db: Session,
        story_id: int,
        user_id: int
    ) -> None:
        """스토리 삭제 (소프트 삭제)"""
        story = await self.get_story_by_id(db, story_id)
        if not story:
            raise NotFoundException("스토리를 찾을 수 없습니다.")
        
        # 작성자 확인
        if story.user_id != user_id:
            raise ForbiddenException("본인의 스토리만 삭제할 수 있습니다.")
        
        story.is_deleted = True
        db.commit()

    async def increment_view_count(self, db: Session, story_id: int) -> None:
        """조회수 증가"""
        db.query(Story).filter(Story.id == story_id).update(
            {Story.view_count: Story.view_count + 1}
        )
        db.commit()

    async def _process_tags(
        self, 
        db: Session, 
        story: Story, 
        tag_names: List[str]
    ) -> None:
        """태그 처리 (생성 또는 연결)"""
        for tag_name in tag_names:
            tag_name = tag_name.strip()
            if not tag_name:
                continue
            
            # 기존 태그 검색
            tag = db.query(Tag).filter(
                func.lower(Tag.name) == func.lower(tag_name)
            ).first()
            
            # 없으면 생성
            if not tag:
                tag = Tag(name=tag_name, usage_count=0)
                db.add(tag)
                db.flush()
            
            # 사용 횟수 증가
            tag.usage_count += 1
            
            # 스토리에 태그 연결
            story.tags.append(tag)

    async def get_stories(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "recent",
        status_filter: Optional[str] = "recruiting",
        tag: Optional[str] = None,
    ) -> tuple[List[Story], int]:
        """
        스토리 목록 조회
        
        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 항목 수
            limit: 조회할 항목 수
            sort_by: 정렬 기준 (recent, deadline, popular)
            status_filter: 상태 필터 (recruiting, all)
            tag: 태그 필터
            
        Returns:
            (스토리 목록, 총 개수)
        """
        query = db.query(Story).options(
            joinedload(Story.user),
            joinedload(Story.tags),
            joinedload(Story.images),
        ).filter(Story.is_deleted == False)
        
        # 상태 필터
        if status_filter == "recruiting":
            query = query.filter(Story.recruitment_status == RecruitmentStatus.RECRUITING)
        
        # 태그 필터
        if tag:
            query = query.join(Story.tags).filter(
                func.lower(Tag.name) == func.lower(tag)
            )
        
        # 정렬
        if sort_by == "deadline":
            # 마감 임박순 (모집중인 것만, 마감일 가까운 순)
            query = query.filter(
                Story.recruitment_status == RecruitmentStatus.RECRUITING
            ).order_by(Story.deadline.asc())
        elif sort_by == "popular":
            # 인기순 (좋아요 많은 순)
            query = query.order_by(desc(Story.like_count), desc(Story.created_at))
        else:
            # 최신순 (기본)
            query = query.order_by(desc(Story.created_at))
        
        # 총 개수
        total = query.count()
        
        # 페이지네이션
        stories = query.offset(skip).limit(limit).all()
        
        return stories, total

    async def count_stories(
        self,
        db: Session,
        status_filter: Optional[str] = "recruiting",
        tag: Optional[str] = None,
    ) -> int:
        """스토리 개수 조회"""
        query = db.query(func.count(Story.id)).filter(Story.is_deleted == False)
        
        if status_filter == "recruiting":
            query = query.filter(Story.recruitment_status == RecruitmentStatus.RECRUITING)
        
        if tag:
            query = query.join(Story.tags).filter(
                func.lower(Tag.name) == func.lower(tag)
            )
        
        return query.scalar()

    async def update_expired_stories(self, db: Session) -> int:
        """마감일 지난 스토리 상태 자동 업데이트"""
        now = datetime.now(timezone.utc)
        
        result = db.query(Story).filter(
            Story.recruitment_status == RecruitmentStatus.RECRUITING,
            Story.deadline < now,
            Story.is_deleted == False
        ).update(
            {Story.recruitment_status: RecruitmentStatus.CLOSED},
            synchronize_session=False
        )
        
        db.commit()
        return result


class LikeService:
    """좋아요 서비스"""

    async def toggle_like(
        self,
        db: Session,
        story_id: int,
        user_id: int
    ) -> tuple[bool, int]:
        """
        좋아요 토글
        
        Returns:
            (is_liked, like_count)
        """
        # 스토리 존재 확인
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.is_deleted == False
        ).first()
        
        if not story:
            raise NotFoundException("스토리를 찾을 수 없습니다.")
        
        # 기존 좋아요 확인
        existing_like = db.query(StoryLike).filter(
            StoryLike.story_id == story_id,
            StoryLike.user_id == user_id
        ).first()
        
        if existing_like:
            # 좋아요 취소
            db.delete(existing_like)
            story.like_count = max(0, story.like_count - 1)
            is_liked = False
        else:
            # 좋아요 추가
            new_like = StoryLike(story_id=story_id, user_id=user_id)
            db.add(new_like)
            story.like_count += 1
            is_liked = True
        
        db.commit()
        return is_liked, story.like_count

    async def is_liked(
        self,
        db: Session,
        story_id: int,
        user_id: int
    ) -> bool:
        """좋아요 여부 확인"""
        return db.query(StoryLike).filter(
            StoryLike.story_id == story_id,
            StoryLike.user_id == user_id
        ).first() is not None


class BookmarkService:
    """북마크 서비스"""

    async def toggle_bookmark(
        self,
        db: Session,
        story_id: int,
        user_id: int
    ) -> tuple[bool, int]:
        """
        북마크 토글
        
        Returns:
            (is_bookmarked, bookmark_count)
        """
        # 스토리 존재 확인
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.is_deleted == False
        ).first()
        
        if not story:
            raise NotFoundException("스토리를 찾을 수 없습니다.")
        
        # 기존 북마크 확인
        existing_bookmark = db.query(StoryBookmark).filter(
            StoryBookmark.story_id == story_id,
            StoryBookmark.user_id == user_id
        ).first()
        
        if existing_bookmark:
            # 북마크 취소
            db.delete(existing_bookmark)
            story.bookmark_count = max(0, story.bookmark_count - 1)
            is_bookmarked = False
        else:
            # 북마크 추가
            new_bookmark = StoryBookmark(story_id=story_id, user_id=user_id)
            db.add(new_bookmark)
            story.bookmark_count += 1
            is_bookmarked = True
        
        db.commit()
        return is_bookmarked, story.bookmark_count

    async def is_bookmarked(
        self,
        db: Session,
        story_id: int,
        user_id: int
    ) -> bool:
        """북마크 여부 확인"""
        return db.query(StoryBookmark).filter(
            StoryBookmark.story_id == story_id,
            StoryBookmark.user_id == user_id
        ).first() is not None

    async def get_bookmarked_stories(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Story], int]:
        """북마크한 스토리 목록 조회"""
        query = db.query(Story).join(StoryBookmark).filter(
            StoryBookmark.user_id == user_id,
            Story.is_deleted == False
        ).options(
            joinedload(Story.user),
            joinedload(Story.tags),
            joinedload(Story.images),
        ).order_by(desc(StoryBookmark.created_at))
        
        total = query.count()
        stories = query.offset(skip).limit(limit).all()
        
        return stories, total


class CommentService:
    """댓글 서비스"""

    async def get_comments(
        self,
        db: Session,
        story_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[StoryComment], int]:
        """댓글 목록 조회"""
        query = db.query(StoryComment).options(
            joinedload(StoryComment.user)
        ).filter(
            StoryComment.story_id == story_id,
            StoryComment.is_deleted == False
        ).order_by(StoryComment.created_at.asc())
        
        total = query.count()
        comments = query.offset(skip).limit(limit).all()
        
        return comments, total

    async def create_comment(
        self,
        db: Session,
        story_id: int,
        user_id: int,
        content: str
    ) -> StoryComment:
        """댓글 생성"""
        # 스토리 존재 확인
        story = db.query(Story).filter(
            Story.id == story_id,
            Story.is_deleted == False
        ).first()
        
        if not story:
            raise NotFoundException("스토리를 찾을 수 없습니다.")
        
        comment = StoryComment(
            story_id=story_id,
            user_id=user_id,
            content=content
        )
        
        db.add(comment)
        story.comment_count += 1
        db.commit()
        db.refresh(comment)
        
        return comment

    async def update_comment(
        self,
        db: Session,
        comment_id: int,
        user_id: int,
        content: str
    ) -> StoryComment:
        """댓글 수정"""
        comment = db.query(StoryComment).options(
            joinedload(StoryComment.user)
        ).filter(
            StoryComment.id == comment_id,
            StoryComment.is_deleted == False
        ).first()
        
        if not comment:
            raise NotFoundException("댓글을 찾을 수 없습니다.")
        
        if comment.user_id != user_id:
            raise ForbiddenException("본인의 댓글만 수정할 수 있습니다.")
        
        comment.content = content
        db.commit()
        db.refresh(comment)
        
        return comment

    async def delete_comment(
        self,
        db: Session,
        comment_id: int,
        user_id: int
    ) -> None:
        """댓글 삭제 (소프트 삭제)"""
        comment = db.query(StoryComment).filter(
            StoryComment.id == comment_id,
            StoryComment.is_deleted == False
        ).first()
        
        if not comment:
            raise NotFoundException("댓글을 찾을 수 없습니다.")
        
        if comment.user_id != user_id:
            raise ForbiddenException("본인의 댓글만 삭제할 수 있습니다.")
        
        comment.is_deleted = True
        
        # 스토리 댓글 수 감소
        story = db.query(Story).filter(Story.id == comment.story_id).first()
        if story:
            story.comment_count = max(0, story.comment_count - 1)
        
        db.commit()


def get_story_service() -> StoryService:
    return StoryService()


def get_like_service() -> LikeService:
    return LikeService()


def get_bookmark_service() -> BookmarkService:
    return BookmarkService()


def get_comment_service() -> CommentService:
    return CommentService()
