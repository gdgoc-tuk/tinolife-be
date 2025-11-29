"""
태그 도메인 모델
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Tag(Base):
    """태그 테이블 - QnA, 티노스토리 등 공통 사용"""

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

    # 관계 - QnA의 question_tags 테이블 통해 연결
    questions = relationship(
        "Question", secondary="question_tags", back_populates="tags"
    )
    # stories는 tinostory/model.py에서 backref="stories"로 자동 생성됨
