from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, select
from datetime import datetime, timezone

from app.domains.qna.model import (
    Category, Question, Answer, AnswerVote, AnswerComment, 
    question_tags, QuestionInterest, QuestionBookmark, Report
)
from app.domains.qna.schema import (
    CategoryCreate, CategoryUpdate, QuestionCreate, QuestionUpdate,
    AnswerCreate, AnswerUpdate, AnswerCommentCreate, AnswerCommentUpdate
)
from app.domains.tags.model import Tag
from app.domains.tags.service import TagService
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


# TagService는 app.domains.tags.service에서 import됨


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
        from app.domains.tino.service import TinoService
        from app.domains.tino.model import TransactionType
        
        category = db.query(Category).filter(Category.id == question_data.category_id).first()
        if not category or not category.is_active:
            raise NotFoundException(f"카테고리를 찾을 수 없습니다: {question_data.category_id}")
        
        if question_data.major_id:
            major = db.query(Major).filter(Major.id == question_data.major_id).first()
            if not major:
                raise NotFoundException(f"전공을 찾을 수 없습니다: {question_data.major_id}")
        
        tino_service = TinoService(db)
        
        # 바운티가 설정된 경우 토큰 차감
        if question_data.bounty > 0:
            tino_service.deduct_token(
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
            from app.domains.tino.model import TinoTransaction as TinoTx
            recent_tx = db.query(TinoTx)\
              .filter(TinoTx.user_id == user_id)\
              .filter(TinoTx.question_id == None)\
              .filter(TinoTx.transaction_type == TransactionType.QUESTION_BOUNTY)\
              .order_by(desc(TinoTx.created_at))\
              .first()
            if recent_tx:
                recent_tx.question_id = question.id
        
        # 질문 등록 보상 1 TINO 지급
        tino_service.charge_token(
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
                
                from app.domains.tino.service import TinoService
                from app.domains.tino.model import TransactionType
                
                tino_service = TinoService(db)
                tino_service.deduct_token(
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
        from app.domains.tino.service import TinoService
        from app.domains.tino.model import TransactionType
        
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
        
        tino_service = TinoService(db)
        tino_service.charge_token(
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
            from app.domains.tino.service import TinoService
            from app.domains.tino.model import TransactionType, TinoTransaction
            
            existing_bonus = db.query(TinoTransaction).filter(
                TinoTransaction.answer_id == answer_id,
                TinoTransaction.transaction_type == TransactionType.ANSWER_LIKE_BONUS
            ).first()
            
            if not existing_bonus:
                tino_service = TinoService(db)
                tino_service.charge_token(
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
        from app.domains.tino.service import TinoService
        from app.domains.tino.model import TransactionType
        
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
        
        # 본인 답변 채택 제한
        if answer.user_id == user_id:
            raise BadRequestException("자신의 답변은 채택할 수 없습니다")
        
        question.accepted_answer_id = answer_id
        question.accepted_at = datetime.now(timezone.utc)
        answer.is_accepted = True
        
        tino_service = TinoService(db)
        
        # 채택 보상: 10 TINO + 바운티
        reward_amount = 10 + question.bounty
        tino_service.charge_token(
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


class InterestService:
    """관심 표시 비즈니스 로직을 처리하는 서비스"""
    
    async def toggle_interest(
        self,
        db: Session,
        question_id: int,
        user_id: int
    ) -> dict:
        """
        질문에 관심 표시 토글
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            user_id: 사용자 ID
            
        Returns:
            관심 표시 결과 (is_interested, interest_count, message)
        """
        # 질문 존재 확인
        question = db.query(Question).filter(
            Question.id == question_id,
            Question.is_deleted == False
        ).first()
        
        if not question:
            raise NotFoundException(f"질문을 찾을 수 없습니다: {question_id}")
        
        # 기존 관심 표시 확인
        existing_interest = db.query(QuestionInterest).filter(
            QuestionInterest.question_id == question_id,
            QuestionInterest.user_id == user_id
        ).first()
        
        if existing_interest:
            # 관심 표시 취소
            db.delete(existing_interest)
            question.interest_count = max(0, question.interest_count - 1)
            db.commit()
            return {
                "question_id": question_id,
                "is_interested": False,
                "interest_count": question.interest_count,
                "message": "관심 표시가 취소되었습니다"
            }
        else:
            # 관심 표시 추가
            new_interest = QuestionInterest(
                question_id=question_id,
                user_id=user_id
            )
            db.add(new_interest)
            question.interest_count += 1
            db.commit()
            return {
                "question_id": question_id,
                "is_interested": True,
                "interest_count": question.interest_count,
                "message": "관심 표시가 추가되었습니다"
            }
    
    async def check_interest(
        self,
        db: Session,
        question_id: int,
        user_id: int
    ) -> bool:
        """
        사용자가 해당 질문에 관심 표시를 했는지 확인
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            user_id: 사용자 ID
            
        Returns:
            관심 표시 여부
        """
        return db.query(QuestionInterest).filter(
            QuestionInterest.question_id == question_id,
            QuestionInterest.user_id == user_id
        ).first() is not None


class BookmarkService:
    """북마크 비즈니스 로직을 처리하는 서비스"""
    
    async def toggle_bookmark(
        self,
        db: Session,
        question_id: int,
        user_id: int
    ) -> dict:
        """
        질문 북마크 토글
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            user_id: 사용자 ID
            
        Returns:
            북마크 결과 (is_bookmarked, message)
        """
        # 질문 존재 확인
        question = db.query(Question).filter(
            Question.id == question_id,
            Question.is_deleted == False
        ).first()
        
        if not question:
            raise NotFoundException(f"질문을 찾을 수 없습니다: {question_id}")
        
        # 기존 북마크 확인
        existing_bookmark = db.query(QuestionBookmark).filter(
            QuestionBookmark.question_id == question_id,
            QuestionBookmark.user_id == user_id
        ).first()
        
        if existing_bookmark:
            # 북마크 삭제
            db.delete(existing_bookmark)
            db.commit()
            return {
                "question_id": question_id,
                "is_bookmarked": False,
                "message": "북마크가 삭제되었습니다"
            }
        else:
            # 북마크 추가
            new_bookmark = QuestionBookmark(
                question_id=question_id,
                user_id=user_id
            )
            db.add(new_bookmark)
            db.commit()
            return {
                "question_id": question_id,
                "is_bookmarked": True,
                "message": "북마크가 추가되었습니다"
            }
    
    async def get_user_bookmarks(
        self,
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        사용자의 북마크 목록 조회
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            page: 페이지 번호
            page_size: 페이지 크기
            
        Returns:
            북마크 목록과 페이지네이션 정보
        """
        query = db.query(QuestionBookmark).filter(
            QuestionBookmark.user_id == user_id
        ).join(Question).filter(
            Question.is_deleted == False
        )
        
        total = query.count()
        
        bookmarks = query.options(
            joinedload(QuestionBookmark.question)
        ).order_by(
            desc(QuestionBookmark.created_at)
        ).offset((page - 1) * page_size).limit(page_size).all()
        
        # 응답 형태로 변환
        bookmark_items = []
        for bookmark in bookmarks:
            bookmark_items.append({
                "id": bookmark.id,
                "question_id": bookmark.question_id,
                "question_title": bookmark.question.title,
                "question_bounty": bookmark.question.bounty,
                "question_answer_count": bookmark.question.answer_count,
                "question_is_accepted": bookmark.question.accepted_answer_id is not None,
                "created_at": bookmark.created_at
            })
        
        return {
            "bookmarks": bookmark_items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def check_bookmark(
        self,
        db: Session,
        question_id: int,
        user_id: int
    ) -> bool:
        """
        사용자가 해당 질문을 북마크했는지 확인
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            user_id: 사용자 ID
            
        Returns:
            북마크 여부
        """
        return db.query(QuestionBookmark).filter(
            QuestionBookmark.question_id == question_id,
            QuestionBookmark.user_id == user_id
        ).first() is not None


class SearchService:
    """검색 비즈니스 로직을 처리하는 서비스"""
    
    async def search_questions(
        self,
        db: Session,
        query: str,
        category_id: Optional[int] = None,
        major_id: Optional[int] = None,
        sort_by: str = "recent",
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """
        질문 검색 (제목, 본문, 태그)
        
        Args:
            db: 데이터베이스 세션
            query: 검색어
            category_id: 카테고리 필터
            major_id: 전공 필터
            sort_by: 정렬 기준 (recent, interest, bounty, unanswered)
            page: 페이지 번호
            page_size: 페이지 크기
            
        Returns:
            검색 결과와 페이지네이션 정보
        """
        search_term = f"%{query}%"
        
        # 기본 쿼리: 삭제되지 않은 질문
        base_query = db.query(Question).filter(Question.is_deleted == False)
        
        # 제목, 본문 검색
        title_content_query = base_query.filter(
            (Question.title.ilike(search_term)) | 
            (Question.content.ilike(search_term))
        )
        
        # 태그로 검색된 질문 ID들
        tag_question_ids = db.query(question_tags.c.question_id).join(
            Tag, Tag.id == question_tags.c.tag_id
        ).filter(
            Tag.name.ilike(search_term),
            Tag.is_active == True
        ).subquery()
        
        # 태그 검색 쿼리
        tag_query = base_query.filter(Question.id.in_(select(tag_question_ids)))
        
        # 제목/본문 검색과 태그 검색 합치기 (UNION)
        from sqlalchemy import union
        
        # 두 쿼리의 결과를 합침
        combined_ids = db.query(Question.id).filter(
            Question.is_deleted == False,
            (
                (Question.title.ilike(search_term)) | 
                (Question.content.ilike(search_term)) |
                (Question.id.in_(select(tag_question_ids)))
            )
        )
        
        # 필터 적용
        if category_id:
            combined_ids = combined_ids.filter(Question.category_id == category_id)
        
        if major_id:
            combined_ids = combined_ids.filter(Question.major_id == major_id)
        
        # 전체 개수
        total = combined_ids.count()
        
        # 실제 질문 조회를 위한 쿼리
        result_query = db.query(Question).filter(
            Question.id.in_(select(combined_ids.subquery()))
        ).options(
            joinedload(Question.category),
            joinedload(Question.major),
            joinedload(Question.tags)
        )
        
        # 정렬
        if sort_by == "interest":
            result_query = result_query.order_by(desc(Question.interest_count), desc(Question.created_at))
        elif sort_by == "bounty":
            result_query = result_query.order_by(desc(Question.bounty), desc(Question.created_at))
        elif sort_by == "unanswered":
            result_query = result_query.order_by(Question.answer_count, desc(Question.created_at))
        else:  # recent
            result_query = result_query.order_by(desc(Question.created_at))
        
        # 페이지네이션
        questions = result_query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "questions": questions,
            "total": total,
            "page": page,
            "page_size": page_size,
            "query": query
        }


def get_category_service() -> CategoryService:
    """CategoryService 인스턴스 반환"""
    return CategoryService()


# get_tag_service는 app.domains.tags.service에서 import


def get_question_service() -> QuestionService:
    """QuestionService 인스턴스 반환"""
    return QuestionService()


def get_answer_service() -> AnswerService:
    """AnswerService 인스턴스 반환"""
    return AnswerService()


def get_answer_comment_service() -> AnswerCommentService:
    """AnswerCommentService 인스턴스 반환"""
    return AnswerCommentService()


def get_interest_service() -> InterestService:
    """InterestService 인스턴스 반환"""
    return InterestService()


def get_bookmark_service() -> BookmarkService:
    """BookmarkService 인스턴스 반환"""
    return BookmarkService()


def get_search_service() -> SearchService:
    """SearchService 인스턴스 반환"""
    return SearchService()


class ReportService:
    """신고 비즈니스 로직을 처리하는 서비스"""
    
    async def report_question(
        self,
        db: Session,
        question_id: int,
        reporter_id: int,
        reason: str,
        description: Optional[str] = None
    ) -> dict:
        """
        질문 신고
        
        Args:
            db: 데이터베이스 세션
            question_id: 질문 ID
            reporter_id: 신고자 ID
            reason: 신고 사유
            description: 상세 설명
            
        Returns:
            신고 결과
        """
        # 질문 존재 확인
        question = db.query(Question).filter(
            Question.id == question_id,
            Question.is_deleted == False
        ).first()
        
        if not question:
            raise NotFoundException(f"질문을 찾을 수 없습니다: {question_id}")
        
        # 자신의 글 신고 방지
        if question.user_id == reporter_id:
            raise BadRequestException("자신의 질문은 신고할 수 없습니다")
        
        # 중복 신고 확인
        existing_report = db.query(Report).filter(
            Report.reporter_id == reporter_id,
            Report.question_id == question_id
        ).first()
        
        if existing_report:
            raise BadRequestException("이미 신고한 질문입니다")
        
        # 신고 생성
        report = Report(
            reporter_id=reporter_id,
            question_id=question_id,
            reason=reason,
            description=description,
            status="PENDING"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return {
            "id": report.id,
            "reporter_id": report.reporter_id,
            "question_id": report.question_id,
            "answer_id": None,
            "reason": report.reason,
            "description": report.description,
            "status": report.status,
            "created_at": report.created_at,
            "message": "신고가 접수되었습니다"
        }
    
    async def report_answer(
        self,
        db: Session,
        answer_id: int,
        reporter_id: int,
        reason: str,
        description: Optional[str] = None
    ) -> dict:
        """
        답변 신고
        
        Args:
            db: 데이터베이스 세션
            answer_id: 답변 ID
            reporter_id: 신고자 ID
            reason: 신고 사유
            description: 상세 설명
            
        Returns:
            신고 결과
        """
        # 답변 존재 확인
        answer = db.query(Answer).filter(
            Answer.id == answer_id,
            Answer.is_deleted == False
        ).first()
        
        if not answer:
            raise NotFoundException(f"답변을 찾을 수 없습니다: {answer_id}")
        
        # 자신의 글 신고 방지
        if answer.user_id == reporter_id:
            raise BadRequestException("자신의 답변은 신고할 수 없습니다")
        
        # 중복 신고 확인
        existing_report = db.query(Report).filter(
            Report.reporter_id == reporter_id,
            Report.answer_id == answer_id
        ).first()
        
        if existing_report:
            raise BadRequestException("이미 신고한 답변입니다")
        
        # 신고 생성
        report = Report(
            reporter_id=reporter_id,
            answer_id=answer_id,
            reason=reason,
            description=description,
            status="PENDING"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        
        return {
            "id": report.id,
            "reporter_id": report.reporter_id,
            "question_id": None,
            "answer_id": report.answer_id,
            "reason": report.reason,
            "description": report.description,
            "status": report.status,
            "created_at": report.created_at,
            "message": "신고가 접수되었습니다"
        }


def get_report_service() -> ReportService:
    """ReportService 인스턴스 반환"""
    return ReportService()
