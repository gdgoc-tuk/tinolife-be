"""
QnA 도메인 모델
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
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


# 중간 테이블 

question_tags = Table(
    "question_tags",
    Base.metadata,
    Column("question_id", Integer, ForeignKey("questions.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True),
    Column(
        "created_at",
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
    comment="질문-태그 다대다 관계",
)


# 카테고리 및 태그 


class Category(Base):
    """질문 카테고리(말머리) 테이블"""

    __tablename__ = "categories"
    __table_args__ = {"comment": "질문 카테고리(말머리)"}

    id = Column(Integer, primary_key=True, index=True, comment="카테고리 ID")
    name = Column(String(50), unique=True, nullable=False, comment="카테고리명")
    display_order = Column(Integer, default=0, nullable=False, comment="표시 순서")
    is_active = Column(Boolean, default=True, nullable=False, comment="활성화 상태")

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
    questions = relationship("Question", back_populates="category")


class Tag(Base):
    """태그 테이블"""

    __tablename__ = "tags"
    __table_args__ = {"comment": "태그"}

    id = Column(Integer, primary_key=True, index=True, comment="태그 ID")
    name = Column(String(50), unique=True, nullable=False, comment="태그명")
    usage_count = Column(Integer, default=0, nullable=False, comment="사용 횟수")
    is_active = Column(Boolean, default=True, nullable=False, comment="활성화 상태")
    is_official = Column(Boolean, default=False, nullable=False, comment="공식 태그 여부")

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
    questions = relationship(
        "Question", secondary="question_tags", back_populates="tags"
    )


class Question(Base):
    """질문 테이블"""

    __tablename__ = "questions"
    __table_args__ = {"comment": "질문"}

    id = Column(Integer, primary_key=True, index=True, comment="질문 ID")

    # 작성자 정보
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="작성자 ID"
    )
    is_anonymous = Column(Boolean, default=False, nullable=False, comment="익명 여부")

    # 질문 내용
    title = Column(String(200), nullable=False, comment="제목")
    content = Column(Text, nullable=False, comment="본문")
    category_id = Column(
        Integer, ForeignKey("categories.id"), nullable=False, comment="카테고리 ID"
    )
    major_id = Column(
        Integer,
        ForeignKey("majors.id"),
        nullable=True,
        comment="전공 ID (null=전공무관, 대분류 제한 없이 전체 전공 선택 가능)",
    )

    # 바운티
    bounty = Column(Integer, default=0, nullable=False, comment="바운티 (TINO 토큰)")

    # 상태
    view_count = Column(Integer, default=0, nullable=False, comment="조회수")
    interest_count = Column(Integer, default=0, nullable=False, comment="관심 수")
    answer_count = Column(Integer, default=0, nullable=False, comment="답변 수")
    is_hidden = Column(Boolean, default=False, nullable=False, comment="숨김 여부")
    is_deleted = Column(Boolean, default=False, nullable=False, comment="삭제 여부")

    # 채택 정보
    accepted_answer_id = Column(
        Integer, ForeignKey("answers.id"), nullable=True, comment="채택된 답변 ID"
    )
    accepted_at = Column(
        DateTime(timezone=True), nullable=True, comment="채택 일시"
    )

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
    category = relationship("Category", back_populates="questions")
    major = relationship("Major")
    tags = relationship("Tag", secondary="question_tags", back_populates="questions")
    answers = relationship(
        "Answer", back_populates="question", foreign_keys="Answer.question_id"
    )
    accepted_answer = relationship(
        "Answer", foreign_keys=[accepted_answer_id], post_update=True
    )
    images = relationship(
        "QuestionImage", back_populates="question", cascade="all, delete-orphan"
    )
    interests = relationship(
        "QuestionInterest", back_populates="question", cascade="all, delete-orphan"
    )
    bookmarks = relationship(
        "QuestionBookmark", back_populates="question", cascade="all, delete-orphan"
    )


class Answer(Base):
    """답변 테이블"""

    __tablename__ = "answers"
    __table_args__ = {"comment": "답변"}

    id = Column(Integer, primary_key=True, index=True, comment="답변 ID")

    # 질문 및 작성자
    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=False, comment="질문 ID"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="작성자 ID"
    )
    is_anonymous = Column(Boolean, default=False, nullable=False, comment="익명 여부")

    # 답변 내용
    content = Column(Text, nullable=False, comment="답변 내용")

    # 상태
    like_count = Column(Integer, default=0, nullable=False, comment="좋아요 수")
    dislike_count = Column(Integer, default=0, nullable=False, comment="싫어요 수")
    comment_count = Column(Integer, default=0, nullable=False, comment="댓글 수")
    is_accepted = Column(Boolean, default=False, nullable=False, comment="채택 여부")
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
    question = relationship(
        "Question", back_populates="answers", foreign_keys=[question_id]
    )
    user = relationship("User")
    votes = relationship("AnswerVote", back_populates="answer", cascade="all, delete-orphan")
    comments = relationship(
        "AnswerComment", back_populates="answer", cascade="all, delete-orphan"
    )
    images = relationship(
        "AnswerImage", back_populates="answer", cascade="all, delete-orphan"
    )


class AnswerVote(Base):
    """답변 투표 테이블"""

    __tablename__ = "answer_votes"
    __table_args__ = (
        UniqueConstraint("answer_id", "user_id", name="uq_answer_user_vote"),
        {"comment": "답변 좋아요/싫어요"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="투표 ID")
    answer_id = Column(
        Integer, ForeignKey("answers.id"), nullable=False, comment="답변 ID"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID"
    )
    vote_type = Column(
        String(10), nullable=False, comment="투표 타입 (LIKE/DISLIKE)"
    )

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
    answer = relationship("Answer", back_populates="votes")
    user = relationship("User")


class AnswerComment(Base):
    """답변 댓글 테이블"""

    __tablename__ = "answer_comments"
    __table_args__ = {"comment": "답변 댓글"}

    id = Column(Integer, primary_key=True, index=True, comment="댓글 ID")

    # 답변 및 작성자
    answer_id = Column(
        Integer, ForeignKey("answers.id"), nullable=False, comment="답변 ID"
    )
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="작성자 ID"
    )
    is_anonymous = Column(Boolean, default=False, nullable=False, comment="익명 여부")

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
    answer = relationship("Answer", back_populates="comments")
    user = relationship("User")


class QuestionInterest(Base):
    """질문 관심 표시 테이블"""

    __tablename__ = "question_interests"
    __table_args__ = (
        UniqueConstraint("question_id", "user_id", name="uq_question_user_interest"),
        {"comment": "질문 관심 표시"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="관심 ID")
    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=False, comment="질문 ID"
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
    question = relationship("Question", back_populates="interests")
    user = relationship("User")


class QuestionBookmark(Base):
    """질문 북마크 테이블"""

    __tablename__ = "question_bookmarks"
    __table_args__ = (
        UniqueConstraint("question_id", "user_id", name="uq_question_user_bookmark"),
        {"comment": "질문 북마크"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="북마크 ID")
    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=False, comment="질문 ID"
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
    question = relationship("Question", back_populates="bookmarks")
    user = relationship("User")


class QuestionImage(Base):
    """질문 이미지 테이블"""

    __tablename__ = "question_images"
    __table_args__ = {"comment": "질문 이미지 메타데이터"}

    id = Column(Integer, primary_key=True, index=True, comment="이미지 ID")
    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=False, comment="질문 ID"
    )

    # 이미지 정보
    image_url = Column(
        String(500), nullable=False, comment="이미지 URL (본문에서 참조)"
    )
    image_key = Column(
        String(200), nullable=True, comment="S3 키 (또는 파일명) - 파일 삭제용"
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
    question = relationship("Question", back_populates="images")


class AnswerImage(Base):
    """답변 이미지 테이블"""

    __tablename__ = "answer_images"
    __table_args__ = {"comment": "답변 이미지 메타데이터"}

    id = Column(Integer, primary_key=True, index=True, comment="이미지 ID")
    answer_id = Column(
        Integer, ForeignKey("answers.id"), nullable=False, comment="답변 ID"
    )

    # 이미지 정보
    image_url = Column(
        String(500), nullable=False, comment="이미지 URL (본문에서 참조)"
    )
    image_key = Column(
        String(200), nullable=True, comment="S3 키 (또는 파일명) - 파일 삭제용"
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
    answer = relationship("Answer", back_populates="images")


class Report(Base):
    """신고 테이블"""

    __tablename__ = "reports"
    __table_args__ = (
        UniqueConstraint("reporter_id", "question_id", name="uq_reporter_question"),
        UniqueConstraint("reporter_id", "answer_id", name="uq_reporter_answer"),
        {"comment": "질문/답변 신고"},
    )

    id = Column(Integer, primary_key=True, index=True, comment="신고 ID")
    reporter_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, comment="신고자 ID"
    )
    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=True, comment="신고된 질문 ID"
    )
    answer_id = Column(
        Integer, ForeignKey("answers.id"), nullable=True, comment="신고된 답변 ID"
    )
    
    # 신고 정보
    reason = Column(
        String(50), nullable=False, comment="신고 사유 (SPAM, ABUSE, INAPPROPRIATE, OTHER)"
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
    question = relationship("Question", backref="reports")
    answer = relationship("Answer", backref="reports")
