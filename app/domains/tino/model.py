"""
TINO 토큰 거래 이력 모델
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class TransactionType:
    """거래 타입 상수"""
    INITIAL = "INITIAL"  # 초기 지급 (신규가입 10 TINO)
    QUESTION_BOUNTY = "QUESTION_BOUNTY"  # 질문 바운티 차감
    QUESTION_REWARD = "QUESTION_REWARD"  # 질문 등록 보상 (+1 TINO)
    ANSWER_REWARD = "ANSWER_REWARD"  # 답변 등록 보상 (+2 TINO)
    ANSWER_ACCEPTED = "ANSWER_ACCEPTED"  # 답변 채택 보상 (+10 TINO + 바운티)
    ANSWER_LIKE_BONUS = "ANSWER_LIKE_BONUS"  # 답변 좋아요 5개 보상 (+3 TINO)
    QUESTION_INTEREST_BONUS = "QUESTION_INTEREST_BONUS"  # 질문 추천 10개 보상 (+3 TINO)
    REFUND = "REFUND"  # 환불
    ADMIN_ADJUST = "ADMIN_ADJUST"  # 관리자 조정
    PURCHASE = "PURCHASE"  # 토큰 구매
    BONUS = "BONUS"  # 보너스 지급
    ATTENDANCE = "ATTENDANCE"  # 출석 보상


class TinoTransaction(Base):
    """TINO 토큰 거래 이력 테이블"""

    __tablename__ = "tino_transactions"
    __table_args__ = {"comment": "TINO 토큰 거래 이력"}

    id = Column(Integer, primary_key=True, index=True, comment="거래 ID")
    user_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True, comment="사용자 ID"
    )

    amount = Column(Integer, nullable=False, comment="거래 금액 (양수=입금, 음수=출금)")
    balance_after = Column(Integer, nullable=False, comment="거래 후 잔액")
    transaction_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="거래 타입 (INITIAL, QUESTION_BOUNTY, ANSWER_REWARD, REFUND, ADMIN_ADJUST, PURCHASE, BONUS)",
    )

    question_id = Column(
        Integer, ForeignKey("questions.id"), nullable=True, comment="관련 질문 ID"
    )
    answer_id = Column(
        Integer, ForeignKey("answers.id"), nullable=True, comment="관련 답변 ID"
    )

    description = Column(String(200), nullable=True, comment="거래 설명")

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="거래 일시",
    )

    user = relationship("User")

    def __repr__(self):
        return f"<TinoTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"
