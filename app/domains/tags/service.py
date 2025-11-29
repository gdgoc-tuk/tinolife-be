"""
태그 도메인 서비스
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.domains.tags.model import Tag


class TagService:
    """태그 비즈니스 로직을 처리하는 서비스"""
    
    async def get_or_create_tag(self, db: Session, tag_name: str) -> Tag:
        """
        태그 조회 또는 생성 (get_or_create 패턴)
        
        Args:
            db: 데이터베이스 세션
            tag_name: 태그명
            
        Returns:
            태그 객체
        """
        tag_name = tag_name.strip().lower()  # 정규화
        
        tag = db.query(Tag).filter(
            func.lower(Tag.name) == tag_name
        ).first()
        
        if not tag:
            tag = Tag(name=tag_name)
            db.add(tag)
            db.flush()
        
        return tag
    
    async def get_tags(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        sort_by: str = "usage",
        include_inactive: bool = False
    ) -> List[Tag]:
        """
        태그 목록 조회
        
        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 항목 수
            limit: 조회할 항목 수
            sort_by: 정렬 기준 ("usage": 사용 빈도순, "recent": 최신순)
            include_inactive: 비활성 태그 포함 여부
            
        Returns:
            태그 목록
        """
        query = db.query(Tag)
        
        if not include_inactive:
            query = query.filter(Tag.is_active == True)
        
        # 정렬
        if sort_by == "usage":
            query = query.order_by(Tag.usage_count.desc(), Tag.id.desc())
        else:  # recent
            query = query.order_by(Tag.created_at.desc())
        
        return query.offset(skip).limit(limit).all()
    
    async def search_tags(
        self,
        db: Session,
        query: str,
        limit: int = 10
    ) -> List[Tag]:
        """
        태그 검색 (자동완성용)
        
        Args:
            db: 데이터베이스 세션
            query: 검색어
            limit: 결과 개수 제한
            
        Returns:
            태그 객체 리스트
        """
        tags = db.query(Tag)\
                .filter(Tag.is_active == True)\
                .filter(Tag.name.ilike(f"%{query}%"))\
                .order_by(Tag.usage_count.desc())\
                .limit(limit)\
                .all()
        
        return tags
    
    async def increment_usage_count(self, db: Session, tag_id: int) -> None:
        """
        태그 사용 횟수 증가
        
        Args:
            db: 데이터베이스 세션
            tag_id: 태그 ID
        """
        db.query(Tag)\
          .filter(Tag.id == tag_id)\
          .update({Tag.usage_count: Tag.usage_count + 1})
        db.flush()
    
    async def count_tags(self, db: Session, include_inactive: bool = False) -> int:
        """
        태그 총 개수 조회
        
        Args:
            db: 데이터베이스 세션
            include_inactive: 비활성 태그 포함 여부
            
        Returns:
            태그 개수
        """
        query = db.query(func.count(Tag.id))
        
        if not include_inactive:
            query = query.filter(Tag.is_active == True)
        
        return query.scalar()


def get_tag_service() -> TagService:
    """TagService 인스턴스 반환"""
    return TagService()
