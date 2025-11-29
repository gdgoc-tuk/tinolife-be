"""
TINO 토큰 관리 서비스
"""
from typing import List, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domains.users.model import User
from app.domains.tino.model import TinoTransaction, TransactionType
from app.domains.tino.schema import (
    TinoTransactionResponse,
    TinoHistoryResponse,
    TRANSACTION_TYPE_DISPLAY,
)
from app.common.exceptions import BadRequestException


class TinoService:
    """TINO 토큰 비즈니스 로직을 처리하는 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_balance(self, user_id: int) -> int:
        """사용자 토큰 잔액 조회"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BadRequestException("사용자를 찾을 수 없습니다")
        return user.tino_balance

    def deduct_token(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        question_id: Optional[int] = None,
        answer_id: Optional[int] = None,
    ) -> TinoTransaction:
        """
        토큰 차감 (동시성 제어 포함)
        """
        if amount <= 0:
            raise BadRequestException("차감 금액은 0보다 커야 합니다")

        user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise BadRequestException("사용자를 찾을 수 없습니다")

        if user.tino_balance < amount:
            raise BadRequestException(
                f"토큰 잔액이 부족합니다. 현재 잔액: {user.tino_balance} TINO, 필요 금액: {amount} TINO"
            )

        user.tino_balance -= amount

        transaction = TinoTransaction(
            user_id=user_id,
            amount=-amount,
            balance_after=user.tino_balance,
            transaction_type=transaction_type,
            question_id=question_id,
            answer_id=answer_id,
            description=description,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def charge_token(
        self,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        question_id: Optional[int] = None,
        answer_id: Optional[int] = None,
    ) -> TinoTransaction:
        """
        토큰 지급 (동시성 제어 포함)
        """
        if amount <= 0:
            raise BadRequestException("지급 금액은 0보다 커야 합니다")

        user = self.db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise BadRequestException("사용자를 찾을 수 없습니다")

        user.tino_balance += amount

        transaction = TinoTransaction(
            user_id=user_id,
            amount=amount,
            balance_after=user.tino_balance,
            transaction_type=transaction_type,
            question_id=question_id,
            answer_id=answer_id,
            description=description,
        )

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)

        return transaction

    def get_history(
        self,
        user: User,
        start_date: date | None,
        end_date: date | None,
        page: int,
        page_size: int,
    ) -> TinoHistoryResponse:
        """TINO 이력 조회"""
        query = self.db.query(TinoTransaction).filter(
            TinoTransaction.user_id == user.id
        )

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            query = query.filter(TinoTransaction.created_at >= start_datetime)

        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(TinoTransaction.created_at <= end_datetime)

        total = query.count()

        transactions = (
            query.order_by(TinoTransaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        transaction_responses = [
            TinoTransactionResponse(
                id=t.id,
                transaction_type=t.transaction_type,
                transaction_type_display=TRANSACTION_TYPE_DISPLAY.get(
                    t.transaction_type, t.transaction_type
                ),
                amount=t.amount,
                balance_after=t.balance_after,
                description=t.description,
                related_question_id=t.question_id,
                related_answer_id=t.answer_id,
                created_at=t.created_at,
            )
            for t in transactions
        ]

        return TinoHistoryResponse(
            transactions=transaction_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_transactions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[List[TinoTransaction], int]:
        """사용자 거래 이력 조회 (레거시 호환)"""
        query = self.db.query(TinoTransaction).filter(
            TinoTransaction.user_id == user_id
        )

        total = query.count()
        transactions = (
            query.order_by(desc(TinoTransaction.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return transactions, total


def get_tino_service(db: Session) -> TinoService:
    """TinoService 인스턴스 반환"""
    return TinoService(db)
