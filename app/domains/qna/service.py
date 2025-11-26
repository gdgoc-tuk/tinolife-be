from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.qna.model import Category, Tag
from app.domains.qna.schema import CategoryCreate, CategoryUpdate
from app.common.exceptions import BadRequestException, NotFoundException


class CategoryService:
    """카테고리 비즈니스 로직을 처리하는 서비스"""
    
    async def get_categories(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Category]:
        """
        카테고리 목록 조회
        
        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 항목 수
            limit: 조회할 항목 수
            include_inactive: 비활성 카테고리 포함 여부
            
        Returns:
            카테고리 목록
        """
        query = db.query(Category)
        
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        
        return query.order_by(Category.display_order, Category.id)\
                    .offset(skip)\
                    .limit(limit)\
                    .all()
    
    async def get_category_by_id(self, db: Session, category_id: int) -> Optional[Category]:
        """
        ID로 카테고리 조회
        
        Args:
            db: 데이터베이스 세션
            category_id: 카테고리 ID
            
        Returns:
            카테고리 객체 또는 None
        """
        return db.query(Category).filter(Category.id == category_id).first()
    
    async def get_category_by_name(self, db: Session, name: str) -> Optional[Category]:
        """
        이름으로 카테고리 조회
        
        Args:
            db: 데이터베이스 세션
            name: 카테고리명
            
        Returns:
            카테고리 객체 또는 None
        """
        return db.query(Category).filter(
            func.lower(Category.name) == func.lower(name)
        ).first()
    
    async def create_category(
        self,
        db: Session,
        category_data: CategoryCreate
    ) -> Category:
        """
        카테고리 생성
        
        Args:
            db: 데이터베이스 세션
            category_data: 카테고리 생성 데이터
            
        Returns:
            생성된 카테고리
            
        Raises:
            BadRequestException: 이름 중복
        """
        # 중복 체크
        existing = self.get_category_by_name(db, category_data.name)
        if existing:
            raise BadRequestException(f"카테고리 '{category_data.name}'이(가) 이미 존재합니다.")
        
        # 생성
        category = Category(
            name=category_data.name,
            display_order=category_data.display_order
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return category
    
    async def update_category(
        self,
        db: Session,
        category_id: int,
        category_data: CategoryUpdate
    ) -> Category:
        """
        카테고리 수정
        
        Args:
            db: 데이터베이스 세션
            category_id: 카테고리 ID
            category_data: 수정 데이터
            
        Returns:
            수정된 카테고리
            
        Raises:
            NotFoundException: 카테고리 없음
            BadRequestException: 이름 중복
        """
        category = self.get_category_by_id(db, category_id)
        if not category:
            raise NotFoundException("카테고리를 찾을 수 없습니다.")
        
        # 이름 중복 체크
        if category_data.name and category_data.name != category.name:
            existing = self.get_category_by_name(db, category_data.name)
            if existing:
                raise BadRequestException(f"카테고리 '{category_data.name}'이(가) 이미 존재합니다.")
        
        # 수정
        if category_data.name is not None:
            category.name = category_data.name
        if category_data.display_order is not None:
            category.display_order = category_data.display_order
        if category_data.is_active is not None:
            category.is_active = category_data.is_active
        
        db.commit()
        db.refresh(category)
        
        return category
    
    async def delete_category(self, db: Session, category_id: int) -> None:
        """
        카테고리 삭제
        
        Args:
            db: 데이터베이스 세션
            category_id: 카테고리 ID
            
        Raises:
            NotFoundException: 카테고리 없음
            BadRequestException: 사용 중인 카테고리
        """
        category = self.get_category_by_id(db, category_id)
        if not category:
            raise NotFoundException("카테고리를 찾을 수 없습니다.")
        
        # 사용 중인지 확인
        from app.domains.qna.model import Question
        question_count = db.query(func.count(Question.id))\
                          .filter(Question.category_id == category_id)\
                          .scalar()
        
        if question_count > 0:
            raise BadRequestException(
                f"사용 중인 카테고리는 삭제할 수 없습니다. (질문 {question_count}개)"
            )
        
        db.delete(category)
        db.commit()
    
    async def count_categories(self, db: Session, include_inactive: bool = False) -> int:
        """
        카테고리 총 개수 조회
        
        Args:
            db: 데이터베이스 세션
            include_inactive: 비활성 카테고리 포함 여부
            
        Returns:
            카테고리 개수
        """
        query = db.query(func.count(Category.id))
        
        if not include_inactive:
            query = query.filter(Category.is_active == True)
        
        return query.scalar()


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
    ) -> List[str]:
        """
        태그 검색 (자동완성용)
        
        Args:
            db: 데이터베이스 세션
            query: 검색어
            limit: 결과 개수 제한
            
        Returns:
            태그명 리스트
        """
        tags = db.query(Tag.name)\
                .filter(Tag.is_active == True)\
                .filter(Tag.name.ilike(f"%{query}%"))\
                .order_by(Tag.usage_count.desc())\
                .limit(limit)\
                .all()
        
        return [tag[0] for tag in tags]
    
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


def get_category_service() -> CategoryService:
    """CategoryService 인스턴스 반환"""
    return CategoryService()


def get_tag_service() -> TagService:
    """TagService 인스턴스 반환"""
    return TagService()
