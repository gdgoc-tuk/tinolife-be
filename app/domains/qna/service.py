from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from datetime import datetime

from app.domains.qna.model import Category, Tag, Question, Answer, AnswerVote, AnswerComment, question_tags
from app.domains.qna.schema import (
    CategoryCreate, CategoryUpdate, QuestionCreate, QuestionUpdate,
    AnswerCreate, AnswerUpdate, AnswerCommentCreate, AnswerCommentUpdate
)
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


class QuestionService:
    """질문 비즈니스 로직을 처리하는 서비스"""
    
    def __init__(self):
        self.tag_service = TagService()
    
    async def create_question(
        self,
        db: Session,
        question_data: QuestionCreate,
        user_id: int
    ) -> Question:
        """
        질문 생성
        
        Args:
            db: 데이터베이스 세션
            question_data: 질문 생성 데이터
            user_id: 작성자 ID
            
        Returns:
            생성된 질문
        """
        from app.domains.qna.model import Category
        from app.domains.majors.model import Major
        from app.domains.users.token_service import TokenService
        from app.domains.users.tino_transaction import TransactionType
        
        category = db.query(Category).filter(Category.id == question_data.category_id).first()
        if not category or not category.is_active:
            raise NotFoundException(f"카테고리를 찾을 수 없습니다: {question_data.category_id}")
        
        if question_data.major_id:
            major = db.query(Major).filter(Major.id == question_data.major_id).first()
            if not major:
                raise NotFoundException(f"전공을 찾을 수 없습니다: {question_data.major_id}")
        
        token_service = TokenService()
        
        # 바운티가 설정된 경우 토큰 차감
        if question_data.bounty > 0:
            await token_service.deduct_token(
                db=db,
                user_id=user_id,
                amount=question_data.bounty,
                transaction_type=TransactionType.QUESTION_BOUNTY,
                description=f"질문 바운티 설정: {question_data.title[:50]}"
            )
        
        question = Question(
            user_id=user_id,
            title=question_data.title,
            content=question_data.content,
            category_id=question_data.category_id,
            major_id=question_data.major_id,
            bounty=question_data.bounty,
            is_anonymous=question_data.is_anonymous,
        )
        
        if question_data.tag_names:
            for tag_name in question_data.tag_names:
                tag = await self.tag_service.get_or_create_tag(db, tag_name)
                question.tags.append(tag)
        
        db.add(question)
        db.flush()
        
        # 바운티가 있는 경우 question_id를 업데이트
        if question_data.bounty > 0:
            from app.domains.users.tino_transaction import TinoTransaction as TinoTx
            recent_tx = db.query(TinoTx)\
              .filter(TinoTx.user_id == user_id)\
              .filter(TinoTx.question_id == None)\
              .filter(TinoTx.transaction_type == TransactionType.QUESTION_BOUNTY)\
              .order_by(desc(TinoTx.created_at))\
              .first()
            if recent_tx:
                recent_tx.question_id = question.id
        
        # 질문 등록 보상 1 TINO 지급
        await token_service.charge_token(
            db=db,
            user_id=user_id,
            amount=1,
            transaction_type=TransactionType.QUESTION_REWARD,
            description="질문 등록 보상",
            question_id=question.id
        )
        
        db.commit()
        db.refresh(question)
        
        return question
    
    async def get_questions(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 20,
        category_id: Optional[int] = None,
        major_id: Optional[int] = None,
        tag_name: Optional[str] = None,
        sort_by: str = "recent"
    ) -> tuple[List[Question], int]:
        """
        질문 목록 조회
        
        Args:
            db: 데이터베이스 세션
            skip: 건너뛸 항목 수
            limit: 조회할 항목 수
            category_id: 카테고리 필터
            major_id: 전공 필터
            tag_name: 태그 필터
            sort_by: 정렬 기준 (recent, interest, bounty, unanswered)
            
        Returns:
            (질문 목록, 전체 개수)
        """
        query = db.query(Question).filter(
            Question.is_deleted == False,
            Question.is_hidden == False
        )
        
        if category_id:
            query = query.filter(Question.category_id == category_id)
        
        if major_id:
            query = query.filter(Question.major_id == major_id)
        
        if tag_name:
            query = query.join(Question.tags).filter(Tag.name == tag_name)
        
        if sort_by == "interest":
            query = query.order_by(desc(Question.interest_count))
        elif sort_by == "bounty":
            query = query.order_by(desc(Question.bounty))
        elif sort_by == "unanswered":
            query = query.order_by(Question.answer_count, desc(Question.created_at))
        else:
            query = query.order_by(desc(Question.created_at))
        
        total = query.count()
        
        questions = query.options(
            joinedload(Question.category),
            joinedload(Question.major),
            joinedload(Question.tags)
        ).offset(skip).limit(limit).all()
        
        return questions, total
    
    async def get_question_by_id(
        self,
        db: Session,
        question_id: int,
        increment_view: bool = False
    ) -> Optional[Question]:
        """
        질문 상세 조회
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            increment_view: 조회수 증가 여부
            
        Returns:
            질문 또는 None
        """
        question = db.query(Question).options(
            joinedload(Question.category),
            joinedload(Question.major),
            joinedload(Question.tags)
        ).filter(Question.id == question_id).first()
        
        if question and increment_view:
            question.view_count += 1
            db.commit()
            db.refresh(question)
        
        return question
    
    async def update_question(
        self,
        db: Session,
        question_id: int,
        question_data: QuestionUpdate,
        user_id: int
    ) -> Question:
        """
        질문 수정
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            question_data: 수정 데이터
            user_id: 요청한 사용자 ID
            
        Returns:
            수정된 질문
        """
        question = await self.get_question_by_id(db, question_id)
        if not question:
            raise NotFoundException(f"질문을 찾을 수 없습니다: {question_id}")
        
        if question.user_id != user_id:
            raise BadRequestException("자신의 질문만 수정할 수 있습니다")
        
        if question.accepted_answer_id:
            raise BadRequestException("채택된 질문은 수정할 수 없습니다")
        
        if question_data.title is not None:
            question.title = question_data.title
        
        if question_data.content is not None:
            question.content = question_data.content
        
        if question_data.category_id is not None:
            from app.domains.qna.model import Category
            category = db.query(Category).filter(Category.id == question_data.category_id).first()
            if not category or not category.is_active:
                raise NotFoundException(f"카테고리를 찾을 수 없습니다: {question_data.category_id}")
            question.category_id = question_data.category_id
        
        if question_data.major_id is not None:
            from app.domains.majors.model import Major
            major = db.query(Major).filter(Major.id == question_data.major_id).first()
            if not major:
                raise NotFoundException(f"전공을 찾을 수 없습니다: {question_data.major_id}")
            question.major_id = question_data.major_id
        
        if question_data.is_anonymous is not None:
            question.is_anonymous = question_data.is_anonymous
        
        if question_data.tag_names is not None:
            question.tags.clear()
            for tag_name in question_data.tag_names:
                tag = await self.tag_service.get_or_create_tag(db, tag_name)
                question.tags.append(tag)
        
        # 바운티 상향 조정 (하향 불가)
        if question_data.bounty is not None:
            if question_data.bounty < question.bounty:
                raise BadRequestException("바운티는 상향 조정만 가능합니다")
            
            if question_data.bounty > question.bounty:
                additional_bounty = question_data.bounty - question.bounty
                
                from app.domains.users.token_service import TokenService
                from app.domains.users.tino_transaction import TransactionType
                
                token_service = TokenService()
                await token_service.deduct_token(
                    db=db,
                    user_id=user_id,
                    amount=additional_bounty,
                    transaction_type=TransactionType.QUESTION_BOUNTY,
                    description=f"바운티 상향 조정: {question.bounty} → {question_data.bounty}",
                    question_id=question_id
                )
                
                question.bounty = question_data.bounty
        
        db.commit()
        db.refresh(question)
        
        return question
    
    async def delete_question(
        self,
        db: Session,
        question_id: int,
        user_id: int
    ) -> None:
        """
        질문 삭제 (소프트 삭제)
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            user_id: 요청한 사용자 ID
        """
        question = await self.get_question_by_id(db, question_id)
        if not question:
            raise NotFoundException(f"질문을 찾을 수 없습니다: {question_id}")
        
        if question.user_id != user_id:
            raise BadRequestException("자신의 질문만 삭제할 수 있습니다")
        
        if question.answer_count > 0:
            raise BadRequestException("답변이 있는 질문은 삭제할 수 없습니다")
        
        question.is_deleted = True
        db.commit()


class AnswerService:
    """답변 비즈니스 로직을 처리하는 서비스"""
    
    async def create_answer(
        self,
        db: Session,
        question_id: int,
        answer_data: AnswerCreate,
        user_id: int
    ) -> Answer:
        """
        답변 생성
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            answer_data: 답변 생성 데이터
            user_id: 작성자 ID
            
        Returns:
            생성된 답변
        """
        from app.domains.users.token_service import TokenService
        from app.domains.users.tino_transaction import TransactionType
        
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise NotFoundException(f"질문을 찾을 수 없습니다: {question_id}")
        
        if question.is_deleted or question.is_hidden:
            raise BadRequestException("삭제되거나 숨겨진 질문에는 답변할 수 없습니다")
        
        if question.accepted_answer_id:
            raise BadRequestException("이미 채택된 질문에는 답변할 수 없습니다")
        
        answer = Answer(
            question_id=question_id,
            user_id=user_id,
            content=answer_data.content,
            is_anonymous=answer_data.is_anonymous,
        )
        
        db.add(answer)
        
        question.answer_count += 1
        
        db.flush()
        
        token_service = TokenService()
        await token_service.charge_token(
            db=db,
            user_id=user_id,
            amount=2,
            transaction_type=TransactionType.ANSWER_REWARD,
            description="답변 등록 보상",
            question_id=question_id,
            answer_id=answer.id
        )
        
        db.commit()
        db.refresh(answer)
        
        return answer
    
    async def get_answers(
        self,
        db: Session,
        question_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[List[Answer], int]:
        """
        질문에 대한 답변 목록 조회
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            skip: 건너뛸 항목 수
            limit: 조회할 항목 수
            
        Returns:
            (답변 목록, 전체 개수)
        """
        query = db.query(Answer).filter(
            Answer.question_id == question_id,
            Answer.is_deleted == False,
            Answer.is_hidden == False
        )
        
        total = query.count()
        
        answers = query.order_by(desc(Answer.like_count), Answer.created_at)\
                      .offset(skip)\
                      .limit(limit)\
                      .all()
        
        return answers, total
    
    async def get_answer_by_id(self, db: Session, answer_id: int) -> Optional[Answer]:
        """답변 ID로 조회"""
        return db.query(Answer).filter(Answer.id == answer_id).first()
    
    async def update_answer(
        self,
        db: Session,
        answer_id: int,
        answer_data: AnswerUpdate,
        user_id: int
    ) -> Answer:
        """
        답변 수정
        
        Args:
            db: 데이터베이스 세션
            answer_id: 답변 ID
            answer_data: 수정 데이터
            user_id: 요청한 사용자 ID
            
        Returns:
            수정된 답변
        """
        answer = await self.get_answer_by_id(db, answer_id)
        if not answer:
            raise NotFoundException(f"답변을 찾을 수 없습니다: {answer_id}")
        
        if answer.user_id != user_id:
            raise BadRequestException("자신의 답변만 수정할 수 있습니다")
        
        if answer.is_accepted:
            raise BadRequestException("채택된 답변은 수정할 수 없습니다")
        
        if answer_data.content is not None:
            answer.content = answer_data.content
        
        if answer_data.is_anonymous is not None:
            answer.is_anonymous = answer_data.is_anonymous
        
        db.commit()
        db.refresh(answer)
        
        return answer
    
    async def delete_answer(
        self,
        db: Session,
        answer_id: int,
        user_id: int
    ) -> None:
        """
        답변 삭제 (소프트 삭제)
        
        Args:
            db: 데이터베이스 세션
            answer_id: 답변 ID
            user_id: 요청한 사용자 ID
        """
        answer = await self.get_answer_by_id(db, answer_id)
        if not answer:
            raise NotFoundException(f"답변을 찾을 수 없습니다: {answer_id}")
        
        if answer.user_id != user_id:
            raise BadRequestException("자신의 답변만 삭제할 수 있습니다")
        
        if answer.is_accepted:
            raise BadRequestException("채택된 답변은 삭제할 수 없습니다")
        
        answer.is_deleted = True
        
        question = db.query(Question).filter(Question.id == answer.question_id).first()
        if question:
            question.answer_count = max(0, question.answer_count - 1)
        
        db.commit()
    
    async def vote_answer(
        self,
        db: Session,
        answer_id: int,
        user_id: int,
        vote_type: str
    ) -> Answer:
        """
        답변에 좋아요/싫어요 투표
        
        Args:
            db: 데이터베이스 세션
            answer_id: 답변 ID
            user_id: 투표한 사용자 ID
            vote_type: 투표 타입 (like/dislike)
            
        Returns:
            업데이트된 답변
        """
        answer = await self.get_answer_by_id(db, answer_id)
        if not answer:
            raise NotFoundException(f"답변을 찾을 수 없습니다: {answer_id}")
        
        if answer.user_id == user_id:
            raise BadRequestException("자신의 답변에는 투표할 수 없습니다")
        
        existing_vote = db.query(AnswerVote).filter(
            AnswerVote.answer_id == answer_id,
            AnswerVote.user_id == user_id
        ).first()
        
        is_like = vote_type == "like"
        current_vote_type = "LIKE" if is_like else "DISLIKE"
        
        if existing_vote:
            existing_is_like = existing_vote.vote_type == "LIKE"
            if existing_is_like == is_like:
                # 같은 투표 취소
                db.delete(existing_vote)
                if is_like:
                    answer.like_count = max(0, answer.like_count - 1)
                else:
                    answer.dislike_count = max(0, answer.dislike_count - 1)
            else:
                # 투표 변경
                if existing_is_like:
                    answer.like_count = max(0, answer.like_count - 1)
                    answer.dislike_count += 1
                else:
                    answer.dislike_count = max(0, answer.dislike_count - 1)
                    answer.like_count += 1
                existing_vote.vote_type = current_vote_type
        else:
            new_vote = AnswerVote(
                answer_id=answer_id,
                user_id=user_id,
                vote_type=current_vote_type
            )
            db.add(new_vote)
            if is_like:
                answer.like_count += 1
            else:
                answer.dislike_count += 1
        
        # 좋아요 5개 달성 시 보상 (최초 1회)
        if is_like and answer.like_count == 5:
            from app.domains.users.token_service import TokenService
            from app.domains.users.tino_transaction import TransactionType, TinoTransaction
            
            existing_bonus = db.query(TinoTransaction).filter(
                TinoTransaction.answer_id == answer_id,
                TinoTransaction.transaction_type == TransactionType.ANSWER_LIKE_BONUS
            ).first()
            
            if not existing_bonus:
                token_service = TokenService()
                await token_service.charge_token(
                    db=db,
                    user_id=answer.user_id,
                    amount=3,
                    transaction_type=TransactionType.ANSWER_LIKE_BONUS,
                    description="답변 좋아요 5개 달성 보상",
                    answer_id=answer_id
                )
        
        db.commit()
        db.refresh(answer)
        
        return answer
    
    async def accept_answer(
        self,
        db: Session,
        question_id: int,
        answer_id: int,
        user_id: int
    ) -> Question:
        """
        답변 채택
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            answer_id: 채택할 답변 ID
            user_id: 요청한 사용자 ID (질문 작성자)
            
        Returns:
            업데이트된 질문
        """
        from app.domains.users.token_service import TokenService
        from app.domains.users.tino_transaction import TransactionType
        
        question = db.query(Question).filter(Question.id == question_id).first()
        if not question:
            raise NotFoundException(f"질문을 찾을 수 없습니다: {question_id}")
        
        if question.user_id != user_id:
            raise BadRequestException("자신의 질문에 대한 답변만 채택할 수 있습니다")
        
        if question.accepted_answer_id:
            raise BadRequestException("이미 채택된 답변이 있습니다")
        
        answer = await self.get_answer_by_id(db, answer_id)
        if not answer:
            raise NotFoundException(f"답변을 찾을 수 없습니다: {answer_id}")
        
        if answer.question_id != question_id:
            raise BadRequestException("해당 질문의 답변이 아닙니다")
        
        if answer.is_deleted or answer.is_hidden:
            raise BadRequestException("삭제되거나 숨겨진 답변은 채택할 수 없습니다")
        
        question.accepted_answer_id = answer_id
        question.accepted_at = datetime.utcnow()
        answer.is_accepted = True
        
        token_service = TokenService()
        
        # 채택 보상: 10 TINO + 바운티
        reward_amount = 10 + question.bounty
        await token_service.charge_token(
            db=db,
            user_id=answer.user_id,
            amount=reward_amount,
            transaction_type=TransactionType.ANSWER_ACCEPTED,
            description=f"답변 채택 보상 (기본 10 + 바운티 {question.bounty})",
            question_id=question_id,
            answer_id=answer_id
        )
        
        db.commit()
        db.refresh(question)
        
        return question


class AnswerCommentService:
    """답변 댓글 비즈니스 로직을 처리하는 서비스"""
    
    async def create_comment(
        self,
        db: Session,
        answer_id: int,
        comment_data: AnswerCommentCreate,
        user_id: int
    ) -> AnswerComment:
        """
        답변 댓글 생성
        
        Args:
            db: 데이터베이스 세션
            answer_id: 답변 ID
            comment_data: 댓글 생성 데이터
            user_id: 작성자 ID
            
        Returns:
            생성된 댓글
        """
        answer = db.query(Answer).filter(Answer.id == answer_id).first()
        if not answer:
            raise NotFoundException(f"답변을 찾을 수 없습니다: {answer_id}")
        
        if answer.is_deleted or answer.is_hidden:
            raise BadRequestException("삭제되거나 숨겨진 답변에는 댓글을 달 수 없습니다")
        
        comment = AnswerComment(
            answer_id=answer_id,
            user_id=user_id,
            content=comment_data.content
        )
        
        db.add(comment)
        db.commit()
        db.refresh(comment)
        
        return comment
    
    async def get_comments(
        self,
        db: Session,
        answer_id: int
    ) -> tuple[List[AnswerComment], int]:
        """
        답변의 댓글 목록 조회
        
        Args:
            db: 데이터베이스 세션
            answer_id: 답변 ID
            
        Returns:
            (댓글 목록, 전체 개수)
        """
        query = db.query(AnswerComment).filter(
            AnswerComment.answer_id == answer_id,
            AnswerComment.is_deleted == False
        )
        
        total = query.count()
        comments = query.order_by(AnswerComment.created_at).all()
        
        return comments, total
    
    async def update_comment(
        self,
        db: Session,
        comment_id: int,
        comment_data: AnswerCommentUpdate,
        user_id: int
    ) -> AnswerComment:
        """
        댓글 수정
        
        Args:
            db: 데이터베이스 세션
            comment_id: 댓글 ID
            comment_data: 수정 데이터
            user_id: 요청한 사용자 ID
            
        Returns:
            수정된 댓글
        """
        comment = db.query(AnswerComment).filter(AnswerComment.id == comment_id).first()
        if not comment:
            raise NotFoundException(f"댓글을 찾을 수 없습니다: {comment_id}")
        
        if comment.user_id != user_id:
            raise BadRequestException("자신의 댓글만 수정할 수 있습니다")
        
        comment.content = comment_data.content
        
        db.commit()
        db.refresh(comment)
        
        return comment
    
    async def delete_comment(
        self,
        db: Session,
        comment_id: int,
        user_id: int
    ) -> None:
        """
        댓글 삭제 (소프트 삭제)
        
        Args:
            db: 데이터베이스 세션
            comment_id: 댓글 ID
            user_id: 요청한 사용자 ID
        """
        comment = db.query(AnswerComment).filter(AnswerComment.id == comment_id).first()
        if not comment:
            raise NotFoundException(f"댓글을 찾을 수 없습니다: {comment_id}")
        
        if comment.user_id != user_id:
            raise BadRequestException("자신의 댓글만 삭제할 수 있습니다")
        
        comment.is_deleted = True
        db.commit()


def get_category_service() -> CategoryService:
    """CategoryService 인스턴스 반환"""
    return CategoryService()


def get_tag_service() -> TagService:
    """TagService 인스턴스 반환"""
    return TagService()


def get_question_service() -> QuestionService:
    """QuestionService 인스턴스 반환"""
    return QuestionService()


def get_answer_service() -> AnswerService:
    """AnswerService 인스턴스 반환"""
    return AnswerService()


def get_answer_comment_service() -> AnswerCommentService:
    """AnswerCommentService 인스턴스 반환"""
    return AnswerCommentService()
