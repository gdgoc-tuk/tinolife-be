from typing import List, Optional
from sqlalchemy.orm import Session
from app.domains.interests.model import Interest
from app.domains.interests.schema import InterestCreate, InterestUpdate


class InterestService:
    """관심사 비즈니스 로직을 처리하는 서비스"""

    async def get_interests(
        self, db: Session, skip: int = 0, limit: int = 100, active_only: bool = True
    ) -> List[Interest]:
        """
        관심사 목록 조회 (페이지네이션)

        관심사는 수가 많을 수 있으므로 페이지네이션 지원
        """
        query = db.query(Interest)

        if active_only:
            query = query.filter(Interest.is_active.is_(True))

        return query.order_by(Interest.name).offset(skip).limit(limit).all()

    async def get_interest_count(self, db: Session, active_only: bool = True) -> int:
        """관심사 총 개수 조회"""
        query = db.query(Interest)

        if active_only:
            query = query.filter(Interest.is_active.is_(True))

        return query.count()

    async def get_interest_by_id(
        self, db: Session, interest_id: int
    ) -> Optional[Interest]:
        """ID로 관심사 조회"""
        return db.query(Interest).filter(Interest.id == interest_id).first()

    async def get_interest_by_name(self, db: Session, name: str) -> Optional[Interest]:
        """이름으로 관심사 조회"""
        return db.query(Interest).filter(Interest.name == name).first()

    async def create_interest(
        self, db: Session, interest_data: InterestCreate
    ) -> Interest:
        """관심사 생성"""
        interest = Interest(**interest_data.model_dump())
        db.add(interest)
        db.commit()
        db.refresh(interest)
        return interest

    async def update_interest(
        self, db: Session, interest_id: int, interest_data: InterestUpdate
    ) -> Optional[Interest]:
        """관심사 업데이트"""
        interest = await self.get_interest_by_id(db, interest_id)
        if not interest:
            return None

        update_data = interest_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(interest, field, value)

        db.commit()
        db.refresh(interest)
        return interest

    async def delete_interest(self, db: Session, interest_id: int) -> bool:
        """관심사 삭제 (소프트 삭제)"""
        interest = await self.get_interest_by_id(db, interest_id)
        if not interest:
            return False

        interest.is_active = False
        db.commit()
        return True


def get_interest_service() -> InterestService:
    """InterestService 의존성 주입"""
    return InterestService()
