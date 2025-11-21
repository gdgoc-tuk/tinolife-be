from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Major(Base):
    """전공 테이블 모델"""
    
    __tablename__ = "majors"
    __table_args__ = {"comment": "전공 정보"}

    id = Column(Integer, primary_key=True, index=True, comment="전공 ID")
    name = Column(String(100), unique=True, nullable=False, comment="전공명")
    code = Column(String(20), nullable=True, comment="전공 코드")
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
    
    # 관계
    users = relationship("User", back_populates="major")

    def __repr__(self):
        return f"<Major(id={self.id}, name={self.name})>"
