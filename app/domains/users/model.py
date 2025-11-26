from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    """사용자 테이블 모델"""

    __tablename__ = "users"
    __table_args__ = {"comment": "사용자 정보"}

    id = Column(Integer, primary_key=True, index=True, comment="사용자 ID")
    email = Column(
        String(255), unique=True, index=True, nullable=False, comment="이메일"
    )
    hashed_password = Column(String(255), nullable=False, comment="해시된 비밀번호")

    # 프로필 정보
    nickname = Column(
        String(50), unique=True, index=True, nullable=False, comment="닉네임"
    )
    student_id = Column(
        String(20), nullable=False, comment="학번"
    )
    grade = Column(Integer, nullable=True, comment="학년 (1-4)")
    major_id = Column(
        Integer, ForeignKey("majors.id"), nullable=True, comment="전공 ID"
    )

    # 상태 정보
    is_active = Column(Boolean, default=True, nullable=False, comment="활성화 상태")
    is_email_verified = Column(
        Boolean, default=False, nullable=False, comment="이메일 인증 여부"
    )

    # 약관 동의
    privacy_policy_agreed_at = Column(
        DateTime(timezone=True), nullable=True, comment="개인정보 처리방침 동의 일시"
    )

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
    major = relationship("Major", back_populates="users")
    interests = relationship(
        "Interest", secondary="user_interests", back_populates="users"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, nickname={self.nickname})>"
