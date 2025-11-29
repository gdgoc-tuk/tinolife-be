"""
TINO 토큰 스키마 정의
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional


TRANSACTION_TYPE_DISPLAY = {
    "INITIAL": "신규가입 보너스",
    "QUESTION_BOUNTY": "질문 바운티 설정",
    "QUESTION_REWARD": "질문 등록 보상",
    "ANSWER_REWARD": "답변 등록 보상",
    "ANSWER_ACCEPTED": "답변 채택 보상",
    "ANSWER_LIKE_BONUS": "답변 좋아요 보상",
    "QUESTION_INTEREST_BONUS": "질문 추천 보상",
    "ATTENDANCE": "출석 체크 보상",
    "REFUND": "환불",
    "ADMIN_ADJUST": "관리자 조정",
    "BONUS": "이벤트 보상",
    "PURCHASE": "토큰 구매",
}


class TinoBalanceResponse(BaseModel):
    """TINO 잔액 응답 스키마"""
    balance: int = Field(..., description="현재 보유 TINO")


class TinoTransactionResponse(BaseModel):
    """TINO 거래 내역 응답 스키마"""
    id: int
    transaction_type: str
    transaction_type_display: str
    amount: int
    balance_after: int
    description: Optional[str] = None
    related_question_id: Optional[int] = None
    related_answer_id: Optional[int] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class TinoHistoryResponse(BaseModel):
    """TINO 이력 응답 스키마"""
    transactions: list[TinoTransactionResponse]
    total: int
    page: int
    page_size: int
