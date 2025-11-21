"""
인증 관련 모델

Note: Auth 도메인은 주로 User 모델을 참조하며,
별도의 테이블이 필요한 경우 (예: RefreshToken, LoginHistory 등)
여기에 정의합니다.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class RefreshToken(Base):
    """리프레시 토큰 테이블"""
    
    __tablename__ = "refresh_tokens"
    __table_args__ = {"comment": "리프레시 토큰 저장"}

    id = Column(Integer, primary_key=True, index=True, comment="토큰 ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID")
    token = Column(Text, unique=True, nullable=False, comment="리프레시 토큰")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="만료 일시")
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="생성 일시"
    )
    
    def __repr__(self):
        return f"<RefreshToken(id={self.id}, user_id={self.user_id})>"


class LoginHistory(Base):
    """로그인 이력 테이블"""
    
    __tablename__ = "login_history"
    __table_args__ = {"comment": "로그인 이력"}

    id = Column(Integer, primary_key=True, index=True, comment="이력 ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="사용자 ID")
    ip_address = Column(String(45), nullable=True, comment="IP 주소")
    user_agent = Column(String(255), nullable=True, comment="User Agent")
    login_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="로그인 일시"
    )
    
    def __repr__(self):
        return f"<LoginHistory(id={self.id}, user_id={self.user_id})>"
