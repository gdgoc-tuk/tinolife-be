"""
인증 관련 모델

Auth 도메인에서 관리하는 테이블:
- RefreshToken: JWT 리프레시 토큰
- LoginHistory: 로그인 이력
- EmailVerification: 이메일 인증 코드
- AllowedEmailDomain: 허용된 이메일 도메인
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean
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


class EmailVerification(Base):
    """이메일 인증 코드 테이블"""
    
    __tablename__ = "email_verifications"
    __table_args__ = {"comment": "이메일 인증 코드"}

    id = Column(Integer, primary_key=True, index=True, comment="인증 ID")
    email = Column(String(255), index=True, nullable=False, comment="이메일")
    code = Column(String(6), nullable=False, comment="6자리 인증 코드")
    expires_at = Column(DateTime(timezone=True), nullable=False, comment="만료 일시")
    is_verified = Column(Boolean, default=False, nullable=False, comment="인증 완료 여부")
    attempt_count = Column(Integer, default=0, nullable=False, comment="시도 횟수")
    resend_count = Column(Integer, default=0, nullable=False, comment="재전송 횟수")
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(), 
        nullable=False,
        comment="생성 일시"
    )
    
    def __repr__(self):
        return f"<EmailVerification(id={self.id}, email={self.email}, is_verified={self.is_verified})>"


class AllowedEmailDomain(Base):
    """허용된 이메일 도메인 테이블"""
    
    __tablename__ = "allowed_email_domains"
    __table_args__ = {"comment": "허용된 이메일 도메인"}

    id = Column(Integer, primary_key=True, index=True, comment="도메인 ID")
    domain = Column(String(100), unique=True, nullable=False, comment="이메일 도메인 (예: @tukorea.ac.kr)")
    university_name = Column(String(100), nullable=True, comment="대학교 이름")
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
        return f"<AllowedEmailDomain(id={self.id}, domain={self.domain})>"
