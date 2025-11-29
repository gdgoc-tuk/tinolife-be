"""
홈 화면 서비스 로직
"""
from typing import Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, or_, and_

from app.domains.qna.model import Question, Category
from app.domains.tinostory.model import Story, RecruitmentStatus, StoryImage
from app.domains.tags.model import Tag
from app.domains.users.model import User
from app.domains.interests.model import Interest, user_interests
from app.domains.home.schema import (
    FeaturedQuestionItem,
    FeaturedQuestionsResponse,
    RecentQuestionItem,
    RecentQuestionsResponse,
    RecommendedStoryItem,
    RecommendedStoriesResponse,
)
from app.domains.qna.schema import CategoryResponse, TagResponse
from app.domains.majors.schema import MajorResponse


# 학년별 키워드 매핑
GRADE_KEYWORDS = {
    1: ["1학년", "새내기", "기초", "교양", "신입생"],
    2: ["2학년", "전공선택", "복수전공", "부전공"],
    3: ["3학년", "인턴", "대외활동", "프로젝트", "공모전"],
    4: ["4학년", "졸업", "취준", "취업", "대학원", "졸작", "졸업작품"],
}

# 키워드별 reason 메시지 매핑
KEYWORD_REASONS = {
    "1학년": "1학년에게 유용한 질문이에요",
    "새내기": "새내기에게 유용한 질문이에요",
    "2학년": "2학년에게 유용한 질문이에요",
    "3학년": "3학년에게 유용한 질문이에요",
    "4학년": "4학년에게 유용한 질문이에요",
    "졸업": "졸업 준비에 도움이 되는 질문이에요",
    "졸작": "졸업 준비에 도움이 되는 질문이에요",
    "졸업작품": "졸업 준비에 도움이 되는 질문이에요",
    "인턴": "취업 준비에 도움이 되는 질문이에요",
    "취준": "취업 준비에 도움이 되는 질문이에요",
    "취업": "취업 준비에 도움이 되는 질문이에요",
    "대학원": "대학원 진학에 관한 질문이에요",
}


class HomeService:
    """홈 화면 서비스"""

    async def get_featured_questions(
        self,
        db: Session,
        user: User,
        limit: int = 5
    ) -> FeaturedQuestionsResponse:
        """
        개인화된 주목 질문 목록 조회
        
        점수 계산:
        - 전공 일치: +50점
        - 학년 관련 키워드: +40점
        - 관심사 태그 매칭: +20점/개
        - 인기도 (interest_count, answer_count, view_count) 가중합
        """
        # 사용자 관심사 태그 이름 목록
        user_interest_names = [interest.name for interest in user.interests]
        
        # 사용자 학년에 해당하는 키워드
        user_grade_keywords = GRADE_KEYWORDS.get(user.grade, []) if user.grade else []
        
        # 기본 질문 쿼리 (삭제/숨김 제외)
        questions = db.query(Question).options(
            joinedload(Question.category),
            joinedload(Question.major),
            joinedload(Question.tags),
        ).filter(
            Question.is_deleted == False,
            Question.is_hidden == False
        ).all()
        
        # 점수 계산 및 정렬
        scored_questions = []
        for question in questions:
            score, reason = self._calculate_question_score(
                question, user, user_interest_names, user_grade_keywords
            )
            if score > 0:  # 관련성이 있는 질문만
                scored_questions.append((question, score, reason))
        
        # 점수 순 정렬
        scored_questions.sort(key=lambda x: x[1], reverse=True)
        
        # 관련성 있는 질문이 부족하면 인기순으로 보충
        if len(scored_questions) < limit:
            popular_questions = db.query(Question).options(
                joinedload(Question.category),
                joinedload(Question.major),
                joinedload(Question.tags),
            ).filter(
                Question.is_deleted == False,
                Question.is_hidden == False
            ).order_by(
                desc(Question.interest_count),
                desc(Question.view_count)
            ).limit(limit * 2).all()
            
            existing_ids = {q[0].id for q in scored_questions}
            for q in popular_questions:
                if q.id not in existing_ids:
                    scored_questions.append((q, 0, "전체 인기 기준으로 보여드려요"))
                    if len(scored_questions) >= limit:
                        break
        
        # 상위 limit개 선택
        top_questions = scored_questions[:limit]
        
        # 응답 변환
        items = []
        for question, score, reason in top_questions:
            items.append(self._to_featured_question_item(question, reason))
        
        return FeaturedQuestionsResponse(
            questions=items,
            total=len(items)
        )

    def _calculate_question_score(
        self,
        question: Question,
        user: User,
        user_interest_names: list[str],
        user_grade_keywords: list[str]
    ) -> tuple[float, str]:
        """질문의 개인화 점수 계산"""
        relevance_score = 0.0
        reasons = []
        
        # 1. 전공 일치 (+50점)
        if question.major_id and user.major_id:
            if question.major_id == user.major_id:
                relevance_score += 50
                reasons.append("같은 학부 학생들이 주목하는 질문이에요")
        
        # 2. 학년 관련 키워드 (+40점)
        question_tag_names = [tag.name for tag in question.tags]
        matched_grade_keyword = None
        for keyword in user_grade_keywords:
            # 태그에서 매칭
            if any(keyword.lower() in tag.lower() for tag in question_tag_names):
                matched_grade_keyword = keyword
                break
            # 제목에서 매칭
            if keyword.lower() in question.title.lower():
                matched_grade_keyword = keyword
                break
        
        if matched_grade_keyword:
            relevance_score += 40
            reason_text = KEYWORD_REASONS.get(
                matched_grade_keyword, 
                f"{user.grade}학년에게 유용한 질문이에요"
            )
            reasons.append(reason_text)
        
        # 3. 관심사 태그 매칭 (+20점/개)
        matched_interests = []
        for interest_name in user_interest_names:
            if any(interest_name.lower() in tag.lower() for tag in question_tag_names):
                relevance_score += 20
                matched_interests.append(interest_name)
        
        if matched_interests:
            reasons.append(f"관심사 태그(#{matched_interests[0]})와 관련된 질문이에요")
        
        # 4. 인기도 점수 계산
        popularity_score = (
            question.interest_count * 3 +
            question.answer_count * 2 +
            question.view_count * 0.1
        )
        
        # 5. 트렌딩 보너스 (24시간 내 생성 & 관심 5개 이상)
        now = datetime.now(timezone.utc)
        if question.created_at:
            created_at = question.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            if (now - created_at) < timedelta(hours=24) and question.interest_count >= 5:
                popularity_score += 30
                if not reasons:
                    reasons.append("최근 24시간 동안 추천이 급증한 질문이에요")
        
        # 최종 점수 = 관련성 × 0.6 + 인기도 × 0.4
        final_score = relevance_score * 0.6 + popularity_score * 0.4
        
        # 가장 우선순위 높은 reason 선택
        primary_reason = reasons[0] if reasons else "전체 인기 기준으로 보여드려요"
        
        return final_score, primary_reason

    def _to_featured_question_item(
        self, 
        question: Question, 
        reason: str
    ) -> FeaturedQuestionItem:
        """Question을 FeaturedQuestionItem으로 변환"""
        # content_preview: 앞 100자
        content_preview = question.content[:100] if question.content else ""
        if len(question.content) > 100:
            content_preview += "..."
        
        return FeaturedQuestionItem(
            id=question.id,
            title=question.title,
            content_preview=content_preview,
            category=CategoryResponse.model_validate(question.category),
            major=MajorResponse.model_validate(question.major) if question.major else None,
            tags=[TagResponse.model_validate(tag) for tag in question.tags],
            bounty=question.bounty,
            interest_count=question.interest_count,
            answer_count=question.answer_count,
            view_count=question.view_count,
            reason=reason,
            created_at=question.created_at
        )

    async def get_recent_questions(
        self,
        db: Session,
        limit: int = 10
    ) -> RecentQuestionsResponse:
        """최신 질문 목록 조회 (단순 최신순)"""
        questions = db.query(Question).options(
            joinedload(Question.category),
            joinedload(Question.major),
            joinedload(Question.tags),
        ).filter(
            Question.is_deleted == False,
            Question.is_hidden == False
        ).order_by(
            desc(Question.created_at)
        ).limit(limit).all()
        
        items = [self._to_recent_question_item(q) for q in questions]
        
        # 전체 개수
        total = db.query(func.count(Question.id)).filter(
            Question.is_deleted == False,
            Question.is_hidden == False
        ).scalar()
        
        return RecentQuestionsResponse(
            questions=items,
            total=total or 0
        )

    def _to_recent_question_item(self, question: Question) -> RecentQuestionItem:
        """Question을 RecentQuestionItem으로 변환"""
        content_preview = question.content[:100] if question.content else ""
        if len(question.content) > 100:
            content_preview += "..."
        
        return RecentQuestionItem(
            id=question.id,
            title=question.title,
            content_preview=content_preview,
            category=CategoryResponse.model_validate(question.category),
            major=MajorResponse.model_validate(question.major) if question.major else None,
            tags=[TagResponse.model_validate(tag) for tag in question.tags],
            bounty=question.bounty,
            interest_count=question.interest_count,
            answer_count=question.answer_count,
            view_count=question.view_count,
            created_at=question.created_at
        )

    async def get_recommended_stories(
        self,
        db: Session,
        user: User,
        limit: int = 5
    ) -> RecommendedStoriesResponse:
        """
        개인화된 추천 스토리 목록 조회
        
        점수 계산:
        - 전공 일치: +50점
        - 관심사 태그 매칭: +20점/개
        - 마감 임박 (D-3 이내): +30점
        - 마감 일주일 이내: +15점
        - 인기도 (like_count)
        """
        user_interest_names = [interest.name for interest in user.interests]
        
        # 모집중인 스토리만 조회
        stories = db.query(Story).options(
            joinedload(Story.user),
            joinedload(Story.tags),
            joinedload(Story.images),
        ).filter(
            Story.is_deleted == False,
            Story.is_hidden == False,
            Story.recruitment_status == RecruitmentStatus.RECRUITING
        ).all()
        
        # 점수 계산 및 정렬
        scored_stories = []
        for story in stories:
            score, reason, days_until = self._calculate_story_score(
                story, user, user_interest_names
            )
            scored_stories.append((story, score, reason, days_until))
        
        # 점수 순 정렬
        scored_stories.sort(key=lambda x: x[1], reverse=True)
        
        # 관련성 있는 스토리가 부족하면 인기순으로 보충
        if len([s for s in scored_stories if s[1] > 0]) < limit:
            for story, score, reason, days_until in scored_stories:
                if score == 0:
                    # reason 업데이트
                    scored_stories = [
                        (s, sc, "전체 인기 기준으로 보여드려요" if sc == 0 else r, d)
                        for s, sc, r, d in scored_stories
                    ]
                    break
        
        # 상위 limit개 선택
        top_stories = scored_stories[:limit]
        
        # 응답 변환
        items = []
        for story, score, reason, days_until in top_stories:
            items.append(self._to_recommended_story_item(story, reason, days_until))
        
        return RecommendedStoriesResponse(
            stories=items,
            total=len(items)
        )

    def _calculate_story_score(
        self,
        story: Story,
        user: User,
        user_interest_names: list[str]
    ) -> tuple[float, str, Optional[int]]:
        """스토리의 개인화 점수 계산"""
        relevance_score = 0.0
        urgency_score = 0.0
        reasons = []
        
        story_tag_names = [tag.name for tag in story.tags]
        
        # 1. 전공 일치 (+50점) - 스토리에 전공 필드가 없으므로 태그로 체크
        # (추후 Story에 major_id 추가 시 업데이트)
        if user.major and user.major.name:
            if any(user.major.name.lower() in tag.lower() for tag in story_tag_names):
                relevance_score += 50
                reasons.append("같은 전공 학생을 찾고 있어요")
        
        # 2. 관심사 태그 매칭 (+20점/개)
        matched_interests = []
        for interest_name in user_interest_names:
            if any(interest_name.lower() in tag.lower() for tag in story_tag_names):
                relevance_score += 20
                matched_interests.append(interest_name)
        
        if matched_interests:
            reasons.append(f"관심사 태그(#{matched_interests[0]})와 관련된 모집글이에요")
        
        # 3. 마감 긴급도 계산
        days_until_deadline = None
        now = datetime.now(timezone.utc)
        
        if story.deadline:
            deadline = story.deadline
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            
            delta = deadline - now
            days_until_deadline = delta.days
            
            if days_until_deadline <= 3:
                urgency_score += 30
                reasons.append("마감이 얼마 남지 않았어요")
            elif days_until_deadline <= 7:
                urgency_score += 15
        
        # 4. 인기도 점수
        popularity_score = story.like_count * 2
        
        # 최종 점수 = 관련성 × 0.5 + 긴급도 × 0.3 + 인기도 × 0.2
        final_score = relevance_score * 0.5 + urgency_score * 0.3 + popularity_score * 0.2
        
        primary_reason = reasons[0] if reasons else "전체 인기 기준으로 보여드려요"
        
        return final_score, primary_reason, days_until_deadline

    def _to_recommended_story_item(
        self, 
        story: Story, 
        reason: str,
        days_until_deadline: Optional[int]
    ) -> RecommendedStoryItem:
        """Story를 RecommendedStoryItem으로 변환"""
        # 썸네일: 첫 번째 이미지
        thumbnail_url = None
        if story.images:
            thumbnail_url = story.images[0].image_url
        
        return RecommendedStoryItem(
            id=story.id,
            title=story.title,
            recruitment_type=story.recruitment_type.value,
            recruitment_status=story.recruitment_status.value,
            thumbnail_url=thumbnail_url,
            tags=[TagResponse.model_validate(tag) for tag in story.tags],
            deadline=story.deadline,
            days_until_deadline=days_until_deadline,
            like_count=story.like_count,
            author_nickname=story.user.nickname if story.user else "알 수 없음",
            reason=reason,
            created_at=story.created_at
        )


def get_home_service() -> HomeService:
    """HomeService 의존성 주입"""
    return HomeService()
