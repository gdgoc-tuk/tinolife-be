from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """사용자 테이블 모델"""
    
    __tablename__ = "users"
    __table_args__ = {"comment": "사용자 정보"}

    id = Column(Integer, primary_key=True, index=True, comment="사용자 ID")
    email = Column(String(255), unique=True, index=True, nullable=False, comment="이메일")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="사용자명")
    full_name = Column(String(100), nullable=True, comment="전체 이름")
    hashed_password = Column(String(255), nullable=False, comment="해시된 비밀번호")
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
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
