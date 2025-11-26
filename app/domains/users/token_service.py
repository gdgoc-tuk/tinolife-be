"""
TINO 토큰 관리 서비스
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.domains.users.model import User
from app.domains.users.tino_transaction import TinoTransaction, TransactionType
from app.common.exceptions import BadRequestException


class TokenService:
    """TINO 토큰 비즈니스 로직을 처리하는 서비스"""
    
    async def get_balance(self, db: Session, user_id: int) -> int:
        """
        사용자 토큰 잔액 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            
        Returns:
            토큰 잔액
        """
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BadRequestException("사용자를 찾을 수 없습니다")
        
        return user.tino_balance
    
    async def deduct_token(
        self,
        db: Session,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        question_id: Optional[int] = None,
        answer_id: Optional[int] = None
    ) -> TinoTransaction:
        """
        토큰 차감 (동시성 제어 포함)
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            amount: 차감할 금액 (양수)
            transaction_type: 거래 타입
            description: 거래 설명
            question_id: 관련 질문 ID
            answer_id: 관련 답변 ID
            
        Returns:
            생성된 거래 이력
            
        Raises:
            BadRequestException: 잔액 부족 시
        """
        if amount <= 0:
            raise BadRequestException("차감 금액은 0보다 커야 합니다")
        
        # 비관적 락을 사용하여 동시성 제어
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise BadRequestException("사용자를 찾을 수 없습니다")
        
        # 잔액 확인
        if user.tino_balance < amount:
            raise BadRequestException(
                f"토큰 잔액이 부족합니다. 현재 잔액: {user.tino_balance} TINO, 필요 금액: {amount} TINO"
            )
        
        # 잔액 차감
        user.tino_balance -= amount
        
        # 거래 이력 생성
        transaction = TinoTransaction(
            user_id=user_id,
            amount=-amount,  # 음수로 저장 (출금)
            balance_after=user.tino_balance,
            transaction_type=transaction_type,
            question_id=question_id,
            answer_id=answer_id,
            description=description
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    async def charge_token(
        self,
        db: Session,
        user_id: int,
        amount: int,
        transaction_type: str,
        description: str,
        question_id: Optional[int] = None,
        answer_id: Optional[int] = None
    ) -> TinoTransaction:
        """
        토큰 지급 (동시성 제어 포함)
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            amount: 지급할 금액 (양수)
            transaction_type: 거래 타입
            description: 거래 설명
            question_id: 관련 질문 ID
            answer_id: 관련 답변 ID
            
        Returns:
            생성된 거래 이력
        """
        if amount <= 0:
            raise BadRequestException("지급 금액은 0보다 커야 합니다")
        
        # 비관적 락을 사용하여 동시성 제어
        user = db.query(User).filter(User.id == user_id).with_for_update().first()
        if not user:
            raise BadRequestException("사용자를 찾을 수 없습니다")
        
        # 잔액 증가
        user.tino_balance += amount
        
        # 거래 이력 생성
        transaction = TinoTransaction(
            user_id=user_id,
            amount=amount,  # 양수로 저장 (입금)
            balance_after=user.tino_balance,
            transaction_type=transaction_type,
            question_id=question_id,
            answer_id=answer_id,
            description=description
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    async def get_transactions(
        self,
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[TinoTransaction], int]:
        """
        사용자 거래 이력 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            skip: 건너뛸 항목 수
            limit: 조회할 항목 수
            
        Returns:
            (거래 이력 목록, 전체 개수)
        """
        query = db.query(TinoTransaction).filter(TinoTransaction.user_id == user_id)
        
        total = query.count()
        transactions = query.order_by(desc(TinoTransaction.created_at))\
                           .offset(skip)\
                           .limit(limit)\
                           .all()
        
        return transactions, total


def get_token_service() -> TokenService:
    """TokenService 인스턴스 반환"""
    return TokenService()
