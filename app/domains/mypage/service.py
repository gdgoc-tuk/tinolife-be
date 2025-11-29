"""
마이페이지 서비스
"""
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.users.model import User
from app.domains.users.tino_transaction import TinoTransaction
from app.domains.qna.model import Question, Answer
from app.domains.tinostory.model import Story, RecruitmentStatus
from app.domains.mypage.schema import (
    ProfileResponse,
    ActivitySummaryResponse,
    TinoSummaryResponse,
    MypageMainResponse,
    TinoTransactionResponse,
    TinoHistoryResponse,
    MyQuestionItem,
    MyQuestionsResponse,
    MyAnswerItem,
    MyAnswersResponse,
    MyStoryItem,
    MyStoriesResponse,
    ProfileUpdateResponse,
    TRANSACTION_TYPE_DISPLAY,
)
from app.domains.majors.schema import MajorResponse
from app.domains.qna.schema import CategoryResponse
from app.domains.tags.schema import TagResponse
from app.common.exceptions import BadRequestException, NotFoundException


class MypageService:
    """마이페이지 서비스"""

    def __init__(self, db: Session):
        self.db = db

    def get_mypage_main(self, user: User) -> MypageMainResponse:
        """마이페이지 메인 정보 조회"""
        profile = ProfileResponse(
            id=user.id,
            nickname=user.nickname,
            email=user.email,
            grade=user.grade,
            major=MajorResponse.model_validate(user.major) if user.major else None,
            student_id=user.student_id,
            profile_image_url=None,
            created_at=user.created_at,
        )

        question_count = self.db.query(func.count(Question.id)).filter(
            Question.user_id == user.id,
            Question.is_deleted == False,
        ).scalar()

        answer_count = self.db.query(func.count(Answer.id)).filter(
            Answer.user_id == user.id,
            Answer.is_deleted == False,
        ).scalar()

        accepted_answer_count = self.db.query(func.count(Answer.id)).filter(
            Answer.user_id == user.id,
            Answer.is_accepted == True,
            Answer.is_deleted == False,
        ).scalar()

        story_count = self.db.query(func.count(Story.id)).filter(
            Story.user_id == user.id,
            Story.is_deleted == False,
        ).scalar()

        activity_summary = ActivitySummaryResponse(
            question_count=question_count,
            answer_count=answer_count,
            accepted_answer_count=accepted_answer_count,
            story_count=story_count,
        )

        tino = TinoSummaryResponse(balance=user.tino_balance)

        return MypageMainResponse(
            profile=profile,
            activity_summary=activity_summary,
            tino=tino,
        )

    def get_tino_history(
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

        transactions = query.order_by(TinoTransaction.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

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

    def get_my_questions(
        self,
        user: User,
        page: int,
        page_size: int,
    ) -> MyQuestionsResponse:
        """내 질문 목록 조회"""
        query = self.db.query(Question).filter(
            Question.user_id == user.id,
            Question.is_deleted == False,
        )

        total = query.count()

        questions = query.order_by(Question.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        question_items = [
            MyQuestionItem(
                id=q.id,
                title=q.title,
                category=CategoryResponse.model_validate(q.category),
                major=MajorResponse.model_validate(q.major) if q.major else None,
                tags=[TagResponse.model_validate(t) for t in q.tags],
                bounty=q.bounty,
                interest_count=q.interest_count,
                answer_count=q.answer_count,
                is_accepted=q.accepted_answer_id is not None,
                created_at=q.created_at,
            )
            for q in questions
        ]

        return MyQuestionsResponse(
            questions=question_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_my_answers(
        self,
        user: User,
        page: int,
        page_size: int,
    ) -> MyAnswersResponse:
        """내 답변 목록 조회"""
        query = self.db.query(Answer).filter(
            Answer.user_id == user.id,
            Answer.is_deleted == False,
        )

        total = query.count()

        answers = query.order_by(Answer.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        answer_items = [
            MyAnswerItem(
                id=a.id,
                question_id=a.question_id,
                question_title=a.question.title if a.question else "",
                content_preview=a.content[:100] if len(a.content) > 100 else a.content,
                like_count=a.like_count,
                is_accepted=a.is_accepted,
                created_at=a.created_at,
            )
            for a in answers
        ]

        return MyAnswersResponse(
            answers=answer_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def get_my_stories(
        self,
        user: User,
        page: int,
        page_size: int,
        status_filter: str,
    ) -> MyStoriesResponse:
        """내 스토리 목록 조회"""
        query = self.db.query(Story).filter(
            Story.user_id == user.id,
            Story.is_deleted == False,
        )

        if status_filter != "all":
            status_map = {
                "recruiting": RecruitmentStatus.RECRUITING,
                "completed": RecruitmentStatus.COMPLETED,
                "closed": RecruitmentStatus.CLOSED,
            }
            if status_filter in status_map:
                query = query.filter(Story.recruitment_status == status_map[status_filter])

        total = query.count()

        stories = query.order_by(Story.created_at.desc()) \
            .offset((page - 1) * page_size) \
            .limit(page_size) \
            .all()

        now = datetime.now(timezone.utc)
        story_items = []
        for s in stories:
            days_until = None
            if s.deadline:
                deadline_aware = s.deadline
                if deadline_aware.tzinfo is None:
                    deadline_aware = deadline_aware.replace(tzinfo=timezone.utc)
                delta = deadline_aware - now
                days_until = max(0, delta.days)

            story_items.append(MyStoryItem(
                id=s.id,
                title=s.title,
                recruitment_type=s.recruitment_type,
                recruitment_status=s.recruitment_status,
                deadline=s.deadline,
                days_until_deadline=days_until,
                like_count=s.like_count,
                comment_count=s.comment_count,
                bookmark_count=s.bookmark_count,
                created_at=s.created_at,
            ))

        return MyStoriesResponse(
            stories=story_items,
            total=total,
            page=page,
            page_size=page_size,
        )

    def update_profile(
        self,
        user: User,
        nickname: str | None,
        grade: int | None,
    ) -> ProfileUpdateResponse:
        """프로필 수정"""
        if nickname is not None and nickname != user.nickname:
            existing = self.db.query(User).filter(
                User.nickname == nickname,
                User.id != user.id,
            ).first()
            if existing:
                raise BadRequestException("이미 사용 중인 닉네임입니다")
            user.nickname = nickname

        if grade is not None:
            user.grade = grade

        self.db.commit()
        self.db.refresh(user)

        return ProfileUpdateResponse(
            id=user.id,
            nickname=user.nickname,
            email=user.email,
            grade=user.grade,
            major=MajorResponse.model_validate(user.major) if user.major else None,
            student_id=user.student_id,
            updated_at=user.updated_at,
        )
