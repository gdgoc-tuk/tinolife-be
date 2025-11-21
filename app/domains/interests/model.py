from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Interest(Base):
    """관심사 테이블 모델"""
    
    __tablename__ = "interests"
    __table_args__ = {"comment": "관심사 키워드"}

    id = Column(Integer, primary_key=True, index=True, comment="관심사 ID")
    name = Column(String(50), unique=True, nullable=False, comment="관심사명")
    is_active = Column(Boolean, default=True, nullable=False, comment="활성화 상태")
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="생성 일시"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="수정 일시"
    )

    def __repr__(self):
        return f"<Interest(id={self.id}, name={self.name})>"


# 사용자-관심사 다대다 관계 테이블
user_interests = Table(
    'user_interests',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('interest_id', Integer, ForeignKey('interests.id'), primary_key=True),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
    comment="사용자-관심사 매핑"
)
