"""
티노스토리 도메인 모델
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Table,
    UniqueConstraint,
    Enum as SQLEnum,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class RecruitmentType(str, enum.Enum):
    """모집 타입"""
    CLUB = "CLUB"           # 동아리
    STUDY = "STUDY"         # 스터디
    PROJECT = "PROJECT"     # 프로젝트
    ACTIVITY = "ACTIVITY"   # 대외활동
    OTHER = "OTHER"         # 기타


class RecruitmentStatus(str, enum.Enum):
    """모집 상태"""
    RECRUITING = "RECRUITING"   # 모집중
    COMPLETED = "COMPLETED"     # 모집완료 (수동)
    CLOSED = "CLOSED"           # 마감 (자동 - 마감일 경과)


# 중간 테이블: Story-Tag 다대다 관계
story_tags = Table(
    "story_tags",
    Base.metadata,
    Column("story_id", Integer, ForeignKey("stories.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    comment="스토리-태그 다대다 관계",
)


class Story(Base):
    """티노스토리 게시글 테이블"""

    __tablename__ = "stories"
    __table_args__ = {"comment": "티노스토리 게시글"}

    id = Column(Integer, primary_key=True, index=True, comment="게시글 ID")

    # 작성자 정보 (익명 불가)
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="작성자 ID"
    )

    # 게시글 내용
    title = Column(String(200), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="본문")

    # 모집 정보
    recruitment_type = Column(
        SQLEnum(RecruitmentType),
        nullable=False,
        comment="모집 타입 (CLUB, STUDY, PROJECT, ACTIVITY, OTHER)"
    )
    recruitment_status = Column(
        SQLEnum(RecruitmentStatus),
        default=RecruitmentStatus.RECRUITING,
        nullable=False,
        comment="모집 상태 (RECRUITING, COMPLETED, CLOSED)"
    )
    deadline = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="모집 마감일"
    )

    # 연락처/링크
    open_chat_link = Column(
        String(500),
        nullable=False,
        comment="오픈채팅 링크 (또는 외부 지원 링크)"
    )

    # 통계
    view_count = Column(Integer, default=0, nullable=False, comment="조회수")
    like_count = Column(Integer, default=0, nullable=False, comment="좋아요 수")
    bookmark_count = Column(Integer, default=0, nullable=False, comment="북마크 수")
    comment_count = Column(Integer, default=0, nullable=False, comment="댓글 수")

    # 상태
    is_hidden = Column(Boolean, default=False, nullable=False, comment="숨김 여부")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="삭제 여부")

    # 타임스탬프
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 일시",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 일시",
    )

    # 관계
    user = relationship("User", foreign_keys=[user_id])
    tags = relationship("Tag", secondary="story_tags", backref="stories")
    images = relationship(
        "StoryImage", back_populates="story", cascade="all, delete-orphan"
    )
    likes = relationship(
        "StoryLike", back_populates="story", cascade="all, delete-orphan"
    )
    bookmarks = relationship(
        "StoryBookmark", back_populates="story", cascade="all, delete-orphan"
    )
    comments = relationship(
        "StoryComment", back_populates="story", cascade="all, delete-orphan"
    )


class StoryImage(Base):
    """스토리 이미지 테이블"""

    __tablename__ = "story_images"
    __table_args__ = {"comment": "스토리 이미지 메타데이터"}

    id = Column(Integer, primary_key=True, index=True, comment="이미지 ID")
    story_id = Column(
        Integer, ForeignKey("stories.id"), nullable=False, comment="스토리 ID"
    )

    # 이미지 정보
    image_url = Column(
        String(500), nullable=False, comment="이미지 URL"
    )
    image_key = Column(
        String(200), nullable=True, comment="S3 키 (또는 파일명) - 파일 삭제용"
    )
    display_order = Column(
        Integer, default=0, nullable=False, comment="표시 순서"
    )
    file_size = Column(Integer, nullable=True, comment="파일 크기 (bytes)")
    mime_type = Column(String(50), nullable=True, comment="MIME 타입 (image/jpeg 등)")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 일시",
    )

    # 관계
    story = relationship("Story", back_populates="images")


class StoryLike(Base):
    """스토리 좋아요 테이블"""

    __tablename__ = "story_likes"
    __table_args__ = (
        UniqueConstraint("story_id", "user_id", name="uq_story_user_like"),
        {"comment": "스토리 좋아요"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="좋아요 ID")
    story_id = Column(
        Integer, ForeignKey("stories.id"), nullable=False, comment="스토리 ID"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 일시",
    )

    # 관계
    story = relationship("Story", back_populates="likes")
    user = relationship("User")


class StoryBookmark(Base):
    """스토리 북마크 테이블"""

    __tablename__ = "story_bookmarks"
    __table_args__ = (
        UniqueConstraint("story_id", "user_id", name="uq_story_user_bookmark"),
        {"comment": "스토리 북마크"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="북마크 ID")
    story_id = Column(
        Integer, ForeignKey("stories.id"), nullable=False, comment="스토리 ID"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID"
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 일시",
    )

    # 관계
    story = relationship("Story", back_populates="bookmarks")
    user = relationship("User")


class StoryComment(Base):
    """스토리 댓글 테이블"""

    __tablename__ = "story_comments"
    __table_args__ = {"comment": "스토리 댓글"}

    id = Column(Integer, primary_key=True, index=True, comment="댓글 ID")

    # 스토리 및 작성자 (익명 불가)
    story_id = Column(
        Integer, ForeignKey("stories.id"), nullable=False, comment="스토리 ID"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="작성자 ID"
    )

    # 댓글 내용
    content = Column(String(500), nullable=False, comment="댓글 내용")

    # 상태
    is_hidden = Column(Boolean, default=False, nullable=False, comment="숨김 여부")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="삭제 여부")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="생성 일시",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 일시",
    )

    # 관계
    story = relationship("Story", back_populates="comments")
    user = relationship("User")


class StoryReport(Base):
    """스토리 신고 테이블"""

    __tablename__ = "story_reports"
    __table_args__ = (
        UniqueConstraint("reporter_id", "story_id", name="uq_reporter_story"),
        UniqueConstraint("reporter_id", "comment_id", name="uq_reporter_story_comment"),
        {"comment": "스토리/댓글 신고"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="신고 ID")
    reporter_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="신고자 ID"
    )
    story_id = Column(
        Integer, ForeignKey("stories.id"), nullable=True, comment="신고된 스토리 ID"
    )
    comment_id = Column(
        Integer, ForeignKey("story_comments.id"), nullable=True, comment="신고된 댓글 ID"
    )

    # 신고 정보
    reason = Column(
        String(50), nullable=False, 
        comment="신고 사유 (SPAM, ABUSE, INAPPROPRIATE, FALSE_INFO, OTHER)"
    )
    description = Column(Text, nullable=True, comment="상세 설명")

    # 처리 상태
    status = Column(
        String(20), default="PENDING", nullable=False,
        comment="처리 상태 (PENDING, REVIEWED, RESOLVED, REJECTED)"
    )
    admin_note = Column(Text, nullable=True, comment="관리자 메모")
    processed_at = Column(DateTime(timezone=True), nullable=True, comment="처리 일시")
    processed_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="처리자 ID")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="신고 일시",
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 일시",
    )

    # 관계
    reporter = relationship("User", foreign_keys=[reporter_id])
    story = relationship("Story", backref="reports")
    comment = relationship("StoryComment", backref="reports")
