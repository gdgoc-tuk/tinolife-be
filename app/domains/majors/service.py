from typing import List, Optional
from sqlalchemy.orm import Session
from app.domains.majors.model import Major
from app.domains.majors.schema import MajorCreate, MajorUpdate


class MajorService:
    """전공 비즈니스 로직을 처리하는 서비스"""

    async def get_majors(self, db: Session, active_only: bool = True) -> List[Major]:
        """
        전공 전체 목록 조회
        """
        query = db.query(Major)

        if active_only:
            query = query.filter(Major.is_active.is_(True))

        return query.order_by(Major.name).all()

    async def get_major_by_id(self, db: Session, major_id: int) -> Optional[Major]:
        """ID로 전공 조회"""
        return db.query(Major).filter(Major.id == major_id).first()

    async def get_major_by_name(self, db: Session, name: str) -> Optional[Major]:
        """이름으로 전공 조회"""
        return db.query(Major).filter(Major.name == name).first()

    async def create_major(self, db: Session, major_data: MajorCreate) -> Major:
        """전공 생성"""
        major = Major(**major_data.model_dump())
        db.add(major)
        db.commit()
        db.refresh(major)
        return major

    async def update_major(
        self, db: Session, major_id: int, major_data: MajorUpdate
    ) -> Optional[Major]:
        """전공 업데이트"""
        major = await self.get_major_by_id(db, major_id)
        if not major:
            return None

        update_data = major_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(major, field, value)

        db.commit()
        db.refresh(major)
        return major

    async def delete_major(self, db: Session, major_id: int) -> bool:
        """전공 삭제 (소프트 삭제)"""
        major = await self.get_major_by_id(db, major_id)
        if not major:
            return False

        major.is_active = False
        db.commit()
        return True


def get_major_service() -> MajorService:
    """MajorService 의존성 주입"""
    return MajorService()
