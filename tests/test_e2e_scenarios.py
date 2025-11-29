"""
E2E 통합 테스트 - 전체 사용자 시나리오 검증
회원가입 → 로그인 → 질문 등록 → 답변 → 바운티 → 채택 플로우를 검증합니다.
"""

import pytest
from fastapi import status
from datetime import datetime, timedelta, timezone


# =============================================================================
# 추가 픽스처
# =============================================================================

@pytest.fixture
def sample_category(db_session):
    """테스트용 QnA 카테고리"""
    from app.domains.qna.model import Category
    
    category = Category(
        name="개발",
        display_order=1,
        is_active=True
    )
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)
    return category


@pytest.fixture
def sample_user_with_tino(db_session, sample_major):
    """테스트용 사용자 (TINO 토큰 보유)"""
    from app.domains.users.model import User
    from app.common.security import hash_password
    
    user = User(
        email="tino_user@test.ac.kr",
        nickname="티노유저",
        student_id="20210001",
        hashed_password=hash_password("testpassword123"),
        grade=2,
        major_id=sample_major.id,
        is_active=True,
        is_email_verified=True,
        tino_balance=50,  # 충분한 TINO 잔액
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def second_user(db_session, sample_major):
    """두 번째 테스트 사용자 (답변자용)"""
    from app.domains.users.model import User
    from app.common.security import hash_password
    
    user = User(
        email="answerer@test.ac.kr",
        nickname="답변자",
        student_id="20210002",
        hashed_password=hash_password("testpassword123"),
        grade=3,
        major_id=sample_major.id,
        is_active=True,
        is_email_verified=True,
        tino_balance=10,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers_tino_user(client, sample_user_with_tino, sample_allowed_domain):
    """TINO 유저의 인증 헤더"""
    response = client.post(
        "/auth/login",
        json={"email": sample_user_with_tino.email, "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_second_user(client, second_user, sample_allowed_domain):
    """두 번째 사용자의 인증 헤더"""
    response = client.post(
        "/auth/login",
        json={"email": second_user.email, "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Phase 1: 인증 테스트
# =============================================================================

class TestAuthFlow:
    """인증 플로우 테스트"""
    
    def test_domain_check_allowed(self, client, sample_allowed_domain):
        """AUTH-001: 허용된 도메인 확인"""
        response = client.post(
            "/auth/check-domain",
            json={"email": "newuser@test.ac.kr"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_allowed"] is True
        assert data["domain"] == "@test.ac.kr"
        assert data["university_name"] == "테스트대학교"
    
    def test_domain_check_not_allowed(self, client):
        """AUTH-002: 허용되지 않은 도메인 확인"""
        response = client.post(
            "/auth/check-domain",
            json={"email": "user@notallowed.com"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_allowed"] is False
    
    def test_login_success(self, client, sample_user, sample_allowed_domain):
        """LOGIN-001: 정상 로그인"""
        response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "testpassword123"}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == sample_user.id
    
    def test_login_wrong_password(self, client, sample_user, sample_allowed_domain):
        """LOGIN-002: 잘못된 비밀번호"""
        response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "wrongpassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_login_nonexistent_email(self, client, sample_allowed_domain):
        """LOGIN-003: 존재하지 않는 이메일"""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@test.ac.kr", "password": "anypassword"}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_token_refresh(self, client, sample_user, sample_allowed_domain):
        """LOGIN-004: 토큰 갱신"""
        # 먼저 로그인
        login_response = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "testpassword123"}
        )
        refresh_token = login_response.json()["refresh_token"]
        
        # 토큰 갱신
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_get_current_user(self, client, auth_headers, sample_user):
        """현재 사용자 정보 조회"""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == sample_user.email
        assert data["nickname"] == sample_user.nickname


# =============================================================================
# Phase 2: QnA 기본 테스트
# =============================================================================

class TestQnABasicFlow:
    """QnA 기본 기능 테스트"""
    
    def test_get_categories(self, client, sample_category):
        """카테고리 목록 조회"""
        response = client.get("/qna/categories")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert any(c["name"] == "개발" for c in data["categories"])
    
    def test_create_question_basic(
        self, client, auth_headers_tino_user, sample_category, sample_user_with_tino, db_session
    ):
        """Q-001: 기본 질문 등록 (바운티 없음)"""
        initial_balance = sample_user_with_tino.tino_balance
        
        response = client.post(
            "/qna/questions",
            json={
                "title": "테스트 질문입니다",
                "content": "질문 내용입니다. 도움 부탁드립니다.",
                "category_id": sample_category.id,
                "bounty": 0,
                "is_anonymous": False
            },
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "테스트 질문입니다"
        assert data["bounty"] == 0
        
        # TINO 보상 확인 (+1)
        db_session.refresh(sample_user_with_tino)
        assert sample_user_with_tino.tino_balance == initial_balance + 1
    
    def test_create_question_with_bounty(
        self, client, auth_headers_tino_user, sample_category, sample_user_with_tino, db_session
    ):
        """Q-002: 바운티 질문 등록"""
        initial_balance = sample_user_with_tino.tino_balance
        bounty_amount = 10
        
        response = client.post(
            "/qna/questions",
            json={
                "title": "바운티 질문입니다",
                "content": "바운티가 걸린 질문입니다.",
                "category_id": sample_category.id,
                "bounty": bounty_amount,
                "is_anonymous": False
            },
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["bounty"] == bounty_amount
        
        # TINO 차감 확인 (-bounty + 1 보상)
        db_session.refresh(sample_user_with_tino)
        expected_balance = initial_balance - bounty_amount + 1
        assert sample_user_with_tino.tino_balance == expected_balance
    
    def test_create_question_with_tags(
        self, client, auth_headers_tino_user, sample_category
    ):
        """Q-003: 태그 포함 질문 등록"""
        response = client.post(
            "/qna/questions",
            json={
                "title": "태그 있는 질문",
                "content": "태그가 포함된 질문입니다.",
                "category_id": sample_category.id,
                "bounty": 0,
                "tag_names": ["python", "fastapi", "backend"]
            },
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["tags"]) == 3
        tag_names = [t["name"] for t in data["tags"]]
        assert "python" in tag_names
        assert "fastapi" in tag_names
    
    def test_create_question_anonymous(
        self, client, auth_headers_tino_user, sample_category
    ):
        """Q-004: 익명 질문 등록"""
        response = client.post(
            "/qna/questions",
            json={
                "title": "익명 질문입니다",
                "content": "익명으로 작성합니다.",
                "category_id": sample_category.id,
                "bounty": 0,
                "is_anonymous": True
            },
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_anonymous"] is True
    
    def test_create_question_insufficient_balance(
        self, client, auth_headers, sample_category, sample_user
    ):
        """Q-005: 잔액 부족 바운티 설정"""
        # sample_user의 기본 TINO는 10
        response = client.post(
            "/qna/questions",
            json={
                "title": "잔액 부족 질문",
                "content": "바운티가 잔액보다 많습니다.",
                "category_id": sample_category.id,
                "bounty": 100,  # 잔액보다 많은 바운티
            },
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_create_question_invalid_category(
        self, client, auth_headers_tino_user
    ):
        """Q-006: 존재하지 않는 카테고리"""
        response = client.post(
            "/qna/questions",
            json={
                "title": "잘못된 카테고리 질문",
                "content": "존재하지 않는 카테고리입니다.",
                "category_id": 99999,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_get_questions_list(
        self, client, auth_headers_tino_user, sample_category
    ):
        """질문 목록 조회"""
        # 먼저 질문 생성
        client.post(
            "/qna/questions",
            json={
                "title": "목록 조회용 질문",
                "content": "목록에서 보여야 합니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        
        # 목록 조회
        response = client.get("/qna/questions")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        assert len(data["questions"]) >= 1
    
    def test_get_question_detail(
        self, client, auth_headers_tino_user, sample_category
    ):
        """질문 상세 조회 (관심/북마크 여부 포함)"""
        # 질문 생성
        create_response = client.post(
            "/qna/questions",
            json={
                "title": "상세 조회용 질문",
                "content": "상세 내용입니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        question_id = create_response.json()["id"]
        
        # 상세 조회 (인증 필요)
        response = client.get(
            f"/qna/questions/{question_id}",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == question_id
        assert data["title"] == "상세 조회용 질문"
        assert data["view_count"] >= 1  # 조회 시 조회수 증가
        assert "is_interested" in data
        assert "is_bookmarked" in data
        assert data["is_interested"] is False
        assert data["is_bookmarked"] is False


# =============================================================================
# Phase 3: 답변 및 상호작용 테스트
# =============================================================================

class TestAnswerFlow:
    """답변 관련 테스트"""
    
    def test_create_answer(
        self, client, auth_headers_tino_user, auth_headers_second_user,
        sample_category, second_user, db_session
    ):
        """A-001: 답변 등록"""
        # 질문 생성 (TINO 유저)
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "답변 테스트용 질문",
                "content": "답변을 기다립니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 두 번째 사용자의 초기 잔액
        initial_balance = second_user.tino_balance
        
        # 답변 등록 (두 번째 사용자)
        response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={
                "content": "도움이 되는 답변입니다.",
                "is_anonymous": False
            },
            headers=auth_headers_second_user
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "도움이 되는 답변입니다."
        assert data["user_id"] == second_user.id
        
        # TINO 보상 확인 (+2)
        db_session.refresh(second_user)
        assert second_user.tino_balance == initial_balance + 2
    
    def test_vote_answer_like(
        self, client, auth_headers_tino_user, auth_headers_second_user, sample_category
    ):
        """A-002: 답변 좋아요"""
        # 질문 생성
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "좋아요 테스트 질문",
                "content": "답변에 좋아요를 테스트합니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 답변 등록 (두 번째 사용자)
        answer_response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={"content": "좋아요 받을 답변입니다."},
            headers=auth_headers_second_user
        )
        answer_id = answer_response.json()["id"]
        
        # 좋아요 투표 (질문 작성자가)
        response = client.post(
            f"/qna/answers/{answer_id}/vote",
            json={"vote_type": "like"},
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["like_count"] == 1
    
    def test_accept_answer(
        self, client, auth_headers_tino_user, auth_headers_second_user,
        sample_category, sample_user_with_tino, second_user, db_session
    ):
        """A-004: 답변 채택"""
        # 바운티 질문 생성
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "채택 테스트 질문",
                "content": "답변을 채택하겠습니다.",
                "category_id": sample_category.id,
                "bounty": 5
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 답변 등록 (두 번째 사용자)
        db_session.refresh(second_user)
        balance_before_answer = second_user.tino_balance
        
        answer_response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={"content": "채택될 답변입니다."},
            headers=auth_headers_second_user
        )
        answer_id = answer_response.json()["id"]
        
        db_session.refresh(second_user)
        balance_after_answer = second_user.tino_balance
        assert balance_after_answer == balance_before_answer + 2  # 답변 보상
        
        # 답변 채택 (질문 작성자가)
        response = client.post(
            f"/qna/questions/{question_id}/accept/{answer_id}",
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["accepted_answer_id"] == answer_id
        
        # 답변자 TINO 보상 확인 (+10 채택 보상 + 5 바운티)
        db_session.refresh(second_user)
        expected_balance = balance_after_answer + 10 + 5
        assert second_user.tino_balance == expected_balance
    
    def test_cannot_accept_own_answer(
        self, client, auth_headers_tino_user, sample_category
    ):
        """A-005: 본인 답변 채택 불가"""
        # 질문 생성
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "자기 답변 채택 테스트",
                "content": "본인 답변은 채택할 수 없습니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 본인이 답변 등록
        answer_response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={"content": "본인의 답변입니다."},
            headers=auth_headers_tino_user
        )
        answer_id = answer_response.json()["id"]
        
        # 본인 답변 채택 시도 - 거부되어야 함
        response = client.post(
            f"/qna/questions/{question_id}/accept/{answer_id}",
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        # 커스텀 에러 응답 형식: {"error": {"code": 400, "message": "..."}}
        error_message = response_data.get("error", {}).get("message", "") or response_data.get("detail", "")
        assert "자신의 답변은 채택할 수 없습니다" in error_message
    
    def test_non_author_cannot_accept(
        self, client, auth_headers_tino_user, auth_headers_second_user, sample_category
    ):
        """A-006: 질문 작성자가 아닌 사용자는 채택 불가"""
        # 질문 생성 (TINO 유저)
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "비작성자 채택 테스트",
                "content": "작성자만 채택할 수 있습니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 답변 등록 (두 번째 사용자)
        answer_response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={"content": "답변입니다."},
            headers=auth_headers_second_user
        )
        answer_id = answer_response.json()["id"]
        
        # 두 번째 사용자가 채택 시도 (질문 작성자가 아님)
        response = client.post(
            f"/qna/questions/{question_id}/accept/{answer_id}",
            headers=auth_headers_second_user
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Phase 4: 바운티 시스템 테스트
# =============================================================================

class TestBountySystem:
    """바운티 시스템 테스트"""
    
    def test_bounty_policy_validation(
        self, client, auth_headers_tino_user, sample_category
    ):
        """B-001: 바운티 정책 검증 (0 또는 5~100)"""
        # 잘못된 바운티 값 (1-4는 허용 안됨)
        response = client.post(
            "/qna/questions",
            json={
                "title": "잘못된 바운티",
                "content": "바운티 정책 위반",
                "category_id": sample_category.id,
                "bounty": 3  # 1-4는 허용되지 않음
            },
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    
    def test_bounty_deduction(
        self, client, auth_headers_tino_user, sample_category, sample_user_with_tino, db_session
    ):
        """B-002: 바운티 차감 검증"""
        initial_balance = sample_user_with_tino.tino_balance
        bounty = 10
        
        response = client.post(
            "/qna/questions",
            json={
                "title": "바운티 차감 테스트",
                "content": "바운티가 차감되어야 합니다.",
                "category_id": sample_category.id,
                "bounty": bounty
            },
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        # 잔액 확인: 기존 - 바운티 + 질문 등록 보상
        db_session.refresh(sample_user_with_tino)
        expected = initial_balance - bounty + 1
        assert sample_user_with_tino.tino_balance == expected
    
    def test_bounty_only_increase(
        self, client, auth_headers_tino_user, sample_category
    ):
        """B-003: 바운티는 상향만 가능"""
        # 바운티 10으로 질문 생성
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "바운티 상향 테스트",
                "content": "바운티를 올리거나 유지할 수 있습니다.",
                "category_id": sample_category.id,
                "bounty": 10
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 바운티 하향 시도
        response = client.put(
            f"/qna/questions/{question_id}",
            json={"bounty": 5},  # 하향 시도
            headers=auth_headers_tino_user
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# Phase 5: 전체 통합 시나리오 테스트
# =============================================================================

class TestFullIntegrationScenario:
    """전체 통합 시나리오 테스트"""
    
    def test_complete_qna_cycle(
        self, client, db_session, sample_major, sample_category, sample_allowed_domain
    ):
        """
        전체 QnA 사이클 테스트
        1. 질문자 생성 (TINO: 10)
        2. 답변자 생성 (TINO: 10)
        3. 질문자가 바운티 15 질문 등록 → TINO: 10 - 15 + 1 = -4 (부족)
           → 바운티 5로 변경 → TINO: 10 - 5 + 1 = 6
        4. 답변자가 답변 등록 → TINO: 10 + 2 = 12
        5. 질문자가 답변 채택 → 답변자 TINO: 12 + 10 + 5 = 27
        """
        from app.domains.users.model import User
        from app.common.security import hash_password
        
        # 1. 질문자 생성
        asker = User(
            email="asker@test.ac.kr",
            nickname="질문자",
            student_id="20230001",
            hashed_password=hash_password("password123"),
            grade=1,
            major_id=sample_major.id,
            is_active=True,
            is_email_verified=True,
            tino_balance=10,
        )
        db_session.add(asker)
        db_session.commit()
        db_session.refresh(asker)
        
        # 2. 답변자 생성
        answerer = User(
            email="answerer2@test.ac.kr",
            nickname="답변자2",
            student_id="20230002",
            hashed_password=hash_password("password123"),
            grade=2,
            major_id=sample_major.id,
            is_active=True,
            is_email_verified=True,
            tino_balance=10,
        )
        db_session.add(answerer)
        db_session.commit()
        db_session.refresh(answerer)
        
        # 로그인
        asker_login = client.post("/auth/login", json={"email": asker.email, "password": "password123"})
        asker_headers = {"Authorization": f"Bearer {asker_login.json()['access_token']}"}
        
        answerer_login = client.post("/auth/login", json={"email": answerer.email, "password": "password123"})
        answerer_headers = {"Authorization": f"Bearer {answerer_login.json()['access_token']}"}
        
        # 3. 질문 등록 (바운티 5)
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "통합 테스트 질문",
                "content": "전체 플로우를 테스트합니다.",
                "category_id": sample_category.id,
                "bounty": 5
            },
            headers=asker_headers
        )
        assert question_response.status_code == status.HTTP_201_CREATED
        question_id = question_response.json()["id"]
        
        # 질문자 잔액 확인: 10 - 5 + 1 = 6
        db_session.refresh(asker)
        assert asker.tino_balance == 6
        
        # 4. 답변 등록
        answer_response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={"content": "도움이 되는 답변입니다!"},
            headers=answerer_headers
        )
        assert answer_response.status_code == status.HTTP_201_CREATED
        answer_id = answer_response.json()["id"]
        
        # 답변자 잔액 확인: 10 + 2 = 12
        db_session.refresh(answerer)
        assert answerer.tino_balance == 12
        
        # 5. 답변 채택
        accept_response = client.post(
            f"/qna/questions/{question_id}/accept/{answer_id}",
            headers=asker_headers
        )
        assert accept_response.status_code == status.HTTP_200_OK
        
        # 최종 답변자 잔액 확인: 12 + 10 + 5 = 27
        db_session.refresh(answerer)
        assert answerer.tino_balance == 27
        
        # 질문 상태 확인 (인증 필요)
        question_detail = client.get(
            f"/qna/questions/{question_id}",
            headers=asker_headers
        )
        assert question_detail.json()["accepted_answer_id"] == answer_id
    
    def test_question_with_multiple_answers(
        self, client, db_session, sample_major, sample_category, sample_allowed_domain
    ):
        """
        여러 답변 시나리오 테스트
        - 질문에 여러 답변이 달리고, 그 중 하나가 채택됨
        """
        from app.domains.users.model import User
        from app.common.security import hash_password
        
        # 사용자들 생성
        asker = User(
            email="multi_asker@test.ac.kr",
            nickname="멀티질문자",
            student_id="20240001",
            hashed_password=hash_password("password123"),
            grade=1,
            major_id=sample_major.id,
            is_active=True,
            is_email_verified=True,
            tino_balance=20,
        )
        
        answerer1 = User(
            email="multi_answerer1@test.ac.kr",
            nickname="멀티답변자1",
            student_id="20240002",
            hashed_password=hash_password("password123"),
            grade=2,
            major_id=sample_major.id,
            is_active=True,
            is_email_verified=True,
            tino_balance=10,
        )
        
        answerer2 = User(
            email="multi_answerer2@test.ac.kr",
            nickname="멀티답변자2",
            student_id="20240003",
            hashed_password=hash_password("password123"),
            grade=3,
            major_id=sample_major.id,
            is_active=True,
            is_email_verified=True,
            tino_balance=10,
        )
        
        db_session.add_all([asker, answerer1, answerer2])
        db_session.commit()
        
        # 로그인
        asker_login = client.post("/auth/login", json={"email": asker.email, "password": "password123"})
        asker_headers = {"Authorization": f"Bearer {asker_login.json()['access_token']}"}
        
        a1_login = client.post("/auth/login", json={"email": answerer1.email, "password": "password123"})
        a1_headers = {"Authorization": f"Bearer {a1_login.json()['access_token']}"}
        
        a2_login = client.post("/auth/login", json={"email": answerer2.email, "password": "password123"})
        a2_headers = {"Authorization": f"Bearer {a2_login.json()['access_token']}"}
        
        # 질문 생성
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "여러 답변 테스트",
                "content": "여러 답변 중 하나를 채택합니다.",
                "category_id": sample_category.id,
                "bounty": 10
            },
            headers=asker_headers
        )
        question_id = question_response.json()["id"]
        
        # 답변 1
        answer1_response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={"content": "첫 번째 답변입니다."},
            headers=a1_headers
        )
        
        # 답변 2
        answer2_response = client.post(
            f"/qna/questions/{question_id}/answers",
            json={"content": "두 번째 답변입니다."},
            headers=a2_headers
        )
        answer2_id = answer2_response.json()["id"]
        
        # 답변 목록 확인
        answers_response = client.get(f"/qna/questions/{question_id}/answers")
        assert answers_response.status_code == status.HTTP_200_OK
        assert answers_response.json()["total"] == 2
        
        # 두 번째 답변 채택
        accept_response = client.post(
            f"/qna/questions/{question_id}/accept/{answer2_id}",
            headers=asker_headers
        )
        assert accept_response.status_code == status.HTTP_200_OK
        
        # 답변자2만 채택 보상 받음
        db_session.refresh(answerer1)
        db_session.refresh(answerer2)
        
        # answerer1: 10 + 2(답변) = 12
        assert answerer1.tino_balance == 12
        # answerer2: 10 + 2(답변) + 10(채택) + 10(바운티) = 32
        assert answerer2.tino_balance == 32


# =============================================================================
# Phase 6: 북마크 및 관심 테스트
# =============================================================================

class TestBookmarkAndInterest:
    """북마크 및 관심 기능 테스트"""
    
    def test_toggle_interest(
        self, client, auth_headers_tino_user, auth_headers_second_user, sample_category
    ):
        """질문 관심 토글"""
        # 질문 생성
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "관심 토글 테스트",
                "content": "관심을 표시합니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 관심 표시 (두 번째 사용자)
        response1 = client.post(
            f"/qna/questions/{question_id}/interest",
            headers=auth_headers_second_user
        )
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["is_interested"] is True
        
        # 상세 조회에서 is_interested 확인
        detail_response = client.get(
            f"/qna/questions/{question_id}",
            headers=auth_headers_second_user
        )
        assert detail_response.json()["is_interested"] is True
        
        # 관심 취소 (토글)
        response2 = client.post(
            f"/qna/questions/{question_id}/interest",
            headers=auth_headers_second_user
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json()["is_interested"] is False
    
    def test_toggle_bookmark(
        self, client, auth_headers_tino_user, auth_headers_second_user, sample_category
    ):
        """질문 북마크 토글"""
        # 질문 생성
        question_response = client.post(
            "/qna/questions",
            json={
                "title": "북마크 토글 테스트",
                "content": "북마크합니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        question_id = question_response.json()["id"]
        
        # 북마크 추가
        response1 = client.post(
            f"/qna/questions/{question_id}/bookmark",
            headers=auth_headers_second_user
        )
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["is_bookmarked"] is True
        
        # 상세 조회에서 is_bookmarked 확인
        detail_response = client.get(
            f"/qna/questions/{question_id}",
            headers=auth_headers_second_user
        )
        assert detail_response.json()["is_bookmarked"] is True
        
        # 북마크 목록 확인
        bookmarks = client.get("/qna/bookmarks", headers=auth_headers_second_user)
        assert bookmarks.status_code == status.HTTP_200_OK
        assert bookmarks.json()["total"] >= 1
        
        # 북마크 삭제 (토글)
        response2 = client.post(
            f"/qna/questions/{question_id}/bookmark",
            headers=auth_headers_second_user
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json()["is_bookmarked"] is False


# =============================================================================
# Phase 7: 검색 테스트
# =============================================================================

class TestSearch:
    """검색 기능 테스트"""
    
    def test_search_questions(
        self, client, auth_headers_tino_user, sample_category
    ):
        """질문 검색"""
        # 검색용 질문 생성
        client.post(
            "/qna/questions",
            json={
                "title": "Python FastAPI 질문입니다",
                "content": "FastAPI로 REST API를 만들고 있습니다.",
                "category_id": sample_category.id,
                "bounty": 0,
                "tag_names": ["python", "fastapi"]
            },
            headers=auth_headers_tino_user
        )
        
        # 검색
        response = client.get("/qna/search?q=FastAPI")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["query"] == "FastAPI"
        # 검색 결과가 있을 수 있음
        assert "questions" in data
        assert "total" in data


# =============================================================================
# Phase 8: 티노스토리 테스트
# =============================================================================

class TestTinoStoryBasicFlow:
    """티노스토리 기본 CRUD 테스트"""

    def test_create_story_success(
        self, client, auth_headers_tino_user
    ):
        """STORY-001: 스토리 생성 성공"""
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        response = client.post(
            "/tinostory",
            json={
                "title": "스터디 팀원 모집합니다",
                "content": "FastAPI 스터디 팀원을 모집합니다. 함께 공부해요!",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/test123",
                "tag_names": ["python", "fastapi", "스터디"]
            },
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "스터디 팀원 모집합니다"
        assert data["recruitment_type"] == "STUDY"
        assert data["recruitment_status"] == "RECRUITING"
        assert len(data["tags"]) == 3
        assert "id" in data

    def test_create_story_missing_required_field(
        self, client, auth_headers_tino_user
    ):
        """STORY-002: 필수 필드 누락 시 에러"""
        response = client.post(
            "/tinostory",
            json={
                "title": "제목만 있는 스토리"
                # content, recruitment_type, deadline, open_chat_link 누락
            },
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_story_unauthorized(self, client):
        """STORY-003: 비인증 사용자 스토리 생성 불가"""
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        response = client.post(
            "/tinostory",
            json={
                "title": "테스트",
                "content": "테스트 내용",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/test"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_story_list(
        self, client, auth_headers_tino_user
    ):
        """STORY-004: 스토리 목록 조회"""
        # 먼저 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        client.post(
            "/tinostory",
            json={
                "title": "목록 테스트 스토리",
                "content": "테스트 내용입니다.",
                "recruitment_type": "PROJECT",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/test"
            },
            headers=auth_headers_tino_user
        )

        # 목록 조회
        response = client.get("/tinostory")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "stories" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_story_list_with_filters(
        self, client, auth_headers_tino_user
    ):
        """STORY-005: 필터링된 스토리 목록 조회"""
        # 다양한 타입의 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        
        # CLUB 타입 스토리
        client.post(
            "/tinostory",
            json={
                "title": "동아리 모집",
                "content": "프로그래밍 동아리입니다.",
                "recruitment_type": "CLUB",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/club",
                "tag_names": ["동아리"]
            },
            headers=auth_headers_tino_user
        )
        
        # STUDY 타입 스토리
        client.post(
            "/tinostory",
            json={
                "title": "스터디 모집",
                "content": "알고리즘 스터디입니다.",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/study",
                "tag_names": ["스터디"]
            },
            headers=auth_headers_tino_user
        )

        # 태그로 필터링
        response = client.get("/tinostory?tag=동아리")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 1
        # 태그 필터링이 적용되었는지 확인
        for story in data["stories"]:
            tag_names = [t["name"] for t in story["tags"]]
            assert "동아리" in tag_names

    def test_get_story_detail(
        self, client, auth_headers_tino_user
    ):
        """STORY-006: 스토리 상세 조회"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "상세 조회 테스트",
                "content": "상세 내용입니다.",
                "recruitment_type": "ACTIVITY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/detail"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 상세 조회 (인증 필요)
        response = client.get(f"/tinostory/{story_id}", headers=auth_headers_tino_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == story_id
        assert data["title"] == "상세 조회 테스트"
        assert data["view_count"] >= 1  # 조회수 증가

    def test_get_story_not_found(self, client, auth_headers_tino_user):
        """STORY-007: 존재하지 않는 스토리 조회"""
        response = client.get("/tinostory/99999", headers=auth_headers_tino_user)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_story_success(
        self, client, auth_headers_tino_user
    ):
        """STORY-008: 스토리 수정 성공"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "수정 전 제목",
                "content": "수정 전 내용",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/before"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 수정
        new_deadline = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
        response = client.put(
            f"/tinostory/{story_id}",
            json={
                "title": "수정 후 제목",
                "content": "수정 후 내용",
                "deadline": new_deadline,
                "open_chat_link": "https://open.kakao.com/after"
            },
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["title"] == "수정 후 제목"
        assert data["content"] == "수정 후 내용"

    def test_update_story_by_other_user(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """STORY-009: 다른 사용자가 스토리 수정 불가"""
        # 스토리 생성 (첫 번째 유저)
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "내 스토리",
                "content": "내 내용",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/mine"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 다른 유저가 수정 시도
        response = client.put(
            f"/tinostory/{story_id}",
            json={"title": "남의 스토리 수정"},
            headers=auth_headers_second_user
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_story_success(
        self, client, auth_headers_tino_user
    ):
        """STORY-010: 스토리 삭제 성공 (소프트 삭제)"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "삭제할 스토리",
                "content": "삭제될 내용",
                "recruitment_type": "OTHER",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/delete"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 삭제
        response = client.delete(
            f"/tinostory/{story_id}",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 삭제된 스토리 조회 불가 (인증 필요)
        get_response = client.get(f"/tinostory/{story_id}", headers=auth_headers_tino_user)
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    def test_complete_recruitment(
        self, client, auth_headers_tino_user
    ):
        """STORY-011: 모집 완료 처리"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "모집 완료 테스트",
                "content": "모집 완료할 스토리",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/complete"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 모집 완료로 변경
        response = client.put(
            f"/tinostory/{story_id}",
            json={"recruitment_status": "COMPLETED"},
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["recruitment_status"] == "COMPLETED"

    def test_upload_image_success(self, client, auth_headers_tino_user):
        """STORY-IMAGE-001: 이미지 업로드 성공"""
        import io
        
        # 테스트용 가짜 이미지 파일 생성 (1x1 PNG)
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        
        response = client.post(
            "/tinostory/images/upload",
            files={"file": ("test_image.png", io.BytesIO(png_header), "image/png")},
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "image_url" in data
        assert "image_key" in data
        assert data["mime_type"] == "image/png"
        assert "tinostory/images" in data["image_key"]
        assert data["message"] == "이미지가 성공적으로 업로드되었습니다"

    def test_upload_image_unauthorized(self, client):
        """STORY-IMAGE-002: 비인증 사용자 이미지 업로드 불가"""
        import io
        
        png_header = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        
        response = client.post(
            "/tinostory/images/upload",
            files={"file": ("test_image.png", io.BytesIO(png_header), "image/png")}
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_upload_image_invalid_type(self, client, auth_headers_tino_user):
        """STORY-IMAGE-003: 허용되지 않는 파일 형식 업로드 실패"""
        import io
        
        # 텍스트 파일로 테스트
        response = client.post(
            "/tinostory/images/upload",
            files={"file": ("test.txt", io.BytesIO(b"hello world"), "text/plain")},
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestTinoStoryInteractions:
    """티노스토리 상호작용 테스트 (좋아요, 북마크, 댓글)"""

    def test_toggle_like(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """LIKE-001: 좋아요 토글"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "좋아요 테스트",
                "content": "좋아요할 스토리",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/like"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 좋아요 추가 (두 번째 유저)
        response1 = client.post(
            f"/tinostory/{story_id}/like",
            headers=auth_headers_second_user
        )
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["is_liked"] is True
        assert response1.json()["like_count"] == 1

        # 좋아요 취소 (토글)
        response2 = client.post(
            f"/tinostory/{story_id}/like",
            headers=auth_headers_second_user
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json()["is_liked"] is False
        assert response2.json()["like_count"] == 0

    def test_toggle_bookmark(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """BOOKMARK-001: 북마크 토글"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "북마크 테스트",
                "content": "북마크할 스토리",
                "recruitment_type": "PROJECT",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/bookmark"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 북마크 추가
        response1 = client.post(
            f"/tinostory/{story_id}/bookmark",
            headers=auth_headers_second_user
        )
        assert response1.status_code == status.HTTP_200_OK
        assert response1.json()["is_bookmarked"] is True

        # 북마크 취소 (토글)
        response2 = client.post(
            f"/tinostory/{story_id}/bookmark",
            headers=auth_headers_second_user
        )
        assert response2.status_code == status.HTTP_200_OK
        assert response2.json()["is_bookmarked"] is False

    def test_get_my_bookmarks(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """BOOKMARK-002: 내 북마크 목록 조회"""
        # 스토리 2개 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        story_ids = []
        for i in range(2):
            create_response = client.post(
                "/tinostory",
                json={
                    "title": f"북마크 목록 테스트 {i+1}",
                    "content": f"내용 {i+1}",
                    "recruitment_type": "STUDY",
                    "deadline": deadline,
                    "open_chat_link": f"https://open.kakao.com/bm{i}"
                },
                headers=auth_headers_tino_user
            )
            story_ids.append(create_response.json()["id"])

        # 두 번째 유저가 북마크
        for story_id in story_ids:
            client.post(
                f"/tinostory/{story_id}/bookmark",
                headers=auth_headers_second_user
            )

        # 북마크 목록 조회
        response = client.get(
            "/tinostory/bookmarks/me",
            headers=auth_headers_second_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 2

    def test_create_comment(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """COMMENT-001: 댓글 작성"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "댓글 테스트",
                "content": "댓글 달 스토리",
                "recruitment_type": "CLUB",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/comment"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 댓글 작성
        response = client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "참여하고 싶습니다!"},
            headers=auth_headers_second_user
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == "참여하고 싶습니다!"
        assert "id" in data

    def test_get_comments(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """COMMENT-002: 댓글 목록 조회"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "댓글 목록 테스트",
                "content": "댓글 여러 개",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/comments"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 댓글 2개 작성
        client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "첫 번째 댓글"},
            headers=auth_headers_second_user
        )
        client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "두 번째 댓글"},
            headers=auth_headers_tino_user
        )

        # 댓글 목록 조회
        response = client.get(f"/tinostory/{story_id}/comments")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] >= 2

    def test_update_comment(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """COMMENT-003: 댓글 수정"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "댓글 수정 테스트",
                "content": "댓글 수정",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/edit"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 댓글 작성
        comment_response = client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "수정 전 댓글"},
            headers=auth_headers_second_user
        )
        comment_id = comment_response.json()["id"]

        # 댓글 수정
        response = client.put(
            f"/tinostory/comments/{comment_id}",
            json={"content": "수정 후 댓글"},
            headers=auth_headers_second_user
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["content"] == "수정 후 댓글"

    def test_update_comment_by_other_user(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """COMMENT-004: 다른 사용자 댓글 수정 불가"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "다른 유저 댓글 수정 테스트",
                "content": "내용",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/other"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 두 번째 유저가 댓글 작성
        comment_response = client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "두 번째 유저 댓글"},
            headers=auth_headers_second_user
        )
        comment_id = comment_response.json()["id"]

        # 첫 번째 유저가 수정 시도
        response = client.put(
            f"/tinostory/comments/{comment_id}",
            json={"content": "남의 댓글 수정"},
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_delete_comment(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """COMMENT-005: 댓글 삭제"""
        # 스토리 생성
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "댓글 삭제 테스트",
                "content": "내용",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/del"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]

        # 댓글 작성
        comment_response = client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "삭제할 댓글"},
            headers=auth_headers_second_user
        )
        comment_id = comment_response.json()["id"]

        # 댓글 삭제
        response = client.delete(
            f"/tinostory/comments/{comment_id}",
            headers=auth_headers_second_user
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT


class TestTinoStoryFullScenario:
    """티노스토리 전체 시나리오 테스트"""

    def test_full_story_lifecycle(
        self, client, auth_headers_tino_user, auth_headers_second_user
    ):
        """SCENARIO-001: 스토리 전체 라이프사이클"""
        deadline = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()

        # 1. 스토리 생성
        create_response = client.post(
            "/tinostory",
            json={
                "title": "알고리즘 스터디 모집",
                "content": "매주 토요일 2시간 알고리즘 문제를 풉니다.",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/algo",
                "tag_names": ["알고리즘", "코딩테스트"]
            },
            headers=auth_headers_tino_user
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        story_id = create_response.json()["id"]

        # 2. 다른 유저가 상세 조회
        detail_response = client.get(
            f"/tinostory/{story_id}",
            headers=auth_headers_second_user
        )
        assert detail_response.status_code == status.HTTP_200_OK
        assert detail_response.json()["view_count"] >= 1

        # 3. 좋아요
        like_response = client.post(
            f"/tinostory/{story_id}/like",
            headers=auth_headers_second_user
        )
        assert like_response.json()["is_liked"] is True

        # 4. 북마크
        bookmark_response = client.post(
            f"/tinostory/{story_id}/bookmark",
            headers=auth_headers_second_user
        )
        assert bookmark_response.json()["is_bookmarked"] is True

        # 5. 댓글 작성
        comment_response = client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "참여하고 싶습니다! 연락 주세요."},
            headers=auth_headers_second_user
        )
        assert comment_response.status_code == status.HTTP_201_CREATED

        # 6. 작성자가 답글 (댓글)
        reply_response = client.post(
            f"/tinostory/{story_id}/comments",
            json={"content": "오픈채팅방 링크로 들어와주세요!"},
            headers=auth_headers_tino_user
        )
        assert reply_response.status_code == status.HTTP_201_CREATED

        # 7. 상세 조회로 상태 확인 (인증 필요)
        final_detail = client.get(f"/tinostory/{story_id}", headers=auth_headers_tino_user)
        data = final_detail.json()
        assert data["like_count"] >= 1
        assert data["bookmark_count"] >= 1
        assert data["comment_count"] >= 2

        # 8. 모집 완료 처리
        complete_response = client.put(
            f"/tinostory/{story_id}",
            json={"recruitment_status": "COMPLETED"},
            headers=auth_headers_tino_user
        )
        assert complete_response.json()["recruitment_status"] == "COMPLETED"

        # 9. 목록에서 모집 완료 상태 확인
        list_response = client.get("/tinostory?status_filter=all")
        assert any(
            item["id"] == story_id 
            for item in list_response.json()["stories"]
        )


# =============================================================================
# Phase 10: 홈 화면 API 테스트
# =============================================================================

class TestHomeAPI:
    """홈 화면 API 테스트"""
    
    def test_featured_questions_unauthorized(self, client):
        """주목 질문 - 비로그인 시 401"""
        response = client.get("/home/featured-questions")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_featured_questions_success(
        self, client, auth_headers_tino_user, sample_category
    ):
        """주목 질문 조회 성공"""
        # 질문 생성
        client.post(
            "/qna/questions",
            json={
                "title": "홈 테스트용 질문",
                "content": "홈 화면에서 보여질 질문입니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        
        # 주목 질문 조회
        response = client.get(
            "/home/featured-questions",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "questions" in data
        assert "total" in data
        
        # 질문이 있으면 reason 필드 확인
        if data["questions"]:
            question = data["questions"][0]
            assert "reason" in question
            assert "content_preview" in question
    
    def test_featured_questions_with_limit(
        self, client, auth_headers_tino_user
    ):
        """주목 질문 - limit 파라미터 테스트"""
        response = client.get(
            "/home/featured-questions?limit=3",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["questions"]) <= 3
    
    def test_recent_questions_success(
        self, client, auth_headers_tino_user, sample_category
    ):
        """최신 질문 조회 성공"""
        # 질문 여러 개 생성
        for i in range(3):
            client.post(
                "/qna/questions",
                json={
                    "title": f"최신 질문 {i}",
                    "content": f"내용 {i}",
                    "category_id": sample_category.id,
                    "bounty": 0
                },
                headers=auth_headers_tino_user
            )
        
        # 최신 질문 조회
        response = client.get(
            "/home/recent-questions",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "questions" in data
        assert "total" in data
        assert len(data["questions"]) >= 3
        
        # 최신순 정렬 확인 (첫 번째가 가장 최근)
        if len(data["questions"]) >= 2:
            first = data["questions"][0]
            second = data["questions"][1]
            assert first["created_at"] >= second["created_at"]
    
    def test_recent_questions_with_limit(
        self, client, auth_headers_tino_user
    ):
        """최신 질문 - limit 파라미터 테스트"""
        response = client.get(
            "/home/recent-questions?limit=5",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["questions"]) <= 5
    
    def test_recommended_stories_success(
        self, client, auth_headers_tino_user
    ):
        """추천 스토리 조회 성공"""
        from datetime import datetime, timedelta
        
        # 모집중인 스토리 생성
        deadline = (datetime.now() + timedelta(days=7)).isoformat()
        client.post(
            "/tinostory",
            json={
                "title": "홈 추천 테스트 스토리",
                "content": "추천 스토리 테스트용입니다.",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/test"
            },
            headers=auth_headers_tino_user
        )
        
        # 추천 스토리 조회
        response = client.get(
            "/home/recommended-stories",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "stories" in data
        assert "total" in data
        
        # 스토리가 있으면 reason, days_until_deadline 필드 확인
        if data["stories"]:
            story = data["stories"][0]
            assert "reason" in story
            assert "days_until_deadline" in story
            assert "author_nickname" in story
            assert story["recruitment_status"] == "RECRUITING"
    
    def test_recommended_stories_only_recruiting(
        self, client, auth_headers_tino_user
    ):
        """추천 스토리 - 모집중인 것만 반환"""
        from datetime import datetime, timedelta
        
        # 모집중인 스토리 생성
        deadline = (datetime.now() + timedelta(days=7)).isoformat()
        create_response = client.post(
            "/tinostory",
            json={
                "title": "모집 완료 테스트",
                "content": "모집 완료될 스토리입니다.",
                "recruitment_type": "PROJECT",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/test2"
            },
            headers=auth_headers_tino_user
        )
        story_id = create_response.json()["id"]
        
        # 모집 완료 처리
        client.put(
            f"/tinostory/{story_id}",
            json={"recruitment_status": "COMPLETED"},
            headers=auth_headers_tino_user
        )
        
        # 추천 스토리 조회 - 완료된 스토리는 제외되어야 함
        response = client.get(
            "/home/recommended-stories",
            headers=auth_headers_tino_user
        )
        data = response.json()
        
        # 모집 완료된 스토리가 목록에 없는지 확인
        story_ids = [s["id"] for s in data["stories"]]
        assert story_id not in story_ids


class TestMypageAPI:
    """마이페이지 API 테스트"""
    
    def test_mypage_main_unauthorized(self, client):
        """마이페이지 메인 - 비로그인 시 401"""
        response = client.get("/mypage")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_mypage_main_success(
        self, client, auth_headers_tino_user, sample_user_with_tino, sample_major
    ):
        """마이페이지 메인 조회 성공"""
        response = client.get("/mypage", headers=auth_headers_tino_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # 프로필 확인
        assert "profile" in data
        assert data["profile"]["nickname"] == sample_user_with_tino.nickname
        assert data["profile"]["email"] == sample_user_with_tino.email
        assert data["profile"]["grade"] == sample_user_with_tino.grade
        
        # 활동 요약 확인
        assert "activity_summary" in data
        assert "question_count" in data["activity_summary"]
        assert "answer_count" in data["activity_summary"]
        assert "accepted_answer_count" in data["activity_summary"]
        assert "story_count" in data["activity_summary"]
        
        # TINO 확인
        assert "tino" in data
        assert data["tino"]["balance"] == sample_user_with_tino.tino_balance
    
    def test_mypage_main_with_activities(
        self, client, auth_headers_tino_user, sample_category
    ):
        """마이페이지 메인 - 활동이 있는 경우"""
        from datetime import datetime, timedelta
        
        # 질문 생성
        client.post(
            "/qna/questions",
            json={
                "title": "마이페이지 테스트 질문",
                "content": "마이페이지 활동 카운트 테스트",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        
        # 스토리 생성
        deadline = (datetime.now() + timedelta(days=7)).isoformat()
        client.post(
            "/tinostory",
            json={
                "title": "마이페이지 테스트 스토리",
                "content": "마이페이지 활동 카운트 테스트",
                "recruitment_type": "STUDY",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/test"
            },
            headers=auth_headers_tino_user
        )
        
        # 마이페이지 조회
        response = client.get("/mypage", headers=auth_headers_tino_user)
        data = response.json()
        
        assert data["activity_summary"]["question_count"] >= 1
        assert data["activity_summary"]["story_count"] >= 1
    
    def test_tino_history_success(
        self, client, auth_headers_tino_user
    ):
        """TINO 이력 조회 성공"""
        response = client.get("/mypage/tino-history", headers=auth_headers_tino_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "transactions" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
    
    def test_tino_history_with_pagination(
        self, client, auth_headers_tino_user
    ):
        """TINO 이력 - 페이지네이션 테스트"""
        response = client.get(
            "/mypage/tino-history?page=1&page_size=5",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["transactions"]) <= 5
    
    def test_tino_history_with_date_filter(
        self, client, auth_headers_tino_user
    ):
        """TINO 이력 - 날짜 필터 테스트"""
        from datetime import date
        
        today = date.today().isoformat()
        response = client.get(
            f"/mypage/tino-history?start_date={today}&end_date={today}",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
    
    def test_my_questions_success(
        self, client, auth_headers_tino_user, sample_category
    ):
        """내 질문 목록 조회 성공"""
        # 질문 생성
        client.post(
            "/qna/questions",
            json={
                "title": "내 질문 목록 테스트",
                "content": "내 질문 목록 테스트용입니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_tino_user
        )
        
        # 내 질문 조회
        response = client.get("/mypage/questions", headers=auth_headers_tino_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "questions" in data
        assert "total" in data
        assert data["total"] >= 1
        
        question = data["questions"][0]
        assert "id" in question
        assert "title" in question
        assert "category" in question
        assert "is_accepted" in question
    
    def test_my_answers_success(
        self, client, auth_headers_tino_user, auth_headers_second_user, sample_category
    ):
        """내 답변 목록 조회 성공"""
        # 다른 유저가 질문 생성
        q_response = client.post(
            "/qna/questions",
            json={
                "title": "답변할 질문",
                "content": "답변 목록 테스트용 질문입니다.",
                "category_id": sample_category.id,
                "bounty": 0
            },
            headers=auth_headers_second_user
        )
        question_id = q_response.json()["id"]
        
        # 내가 답변 작성
        client.post(
            f"/qna/questions/{question_id}/answers",
            json={
                "content": "내 답변 목록 테스트용 답변입니다. 답변 내용이 길어야 테스트가 정확합니다."
            },
            headers=auth_headers_tino_user
        )
        
        # 내 답변 조회
        response = client.get("/mypage/answers", headers=auth_headers_tino_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "answers" in data
        assert "total" in data
        assert data["total"] >= 1
        
        answer = data["answers"][0]
        assert "id" in answer
        assert "question_id" in answer
        assert "question_title" in answer
        assert "content_preview" in answer
        assert "is_accepted" in answer
    
    def test_my_stories_success(
        self, client, auth_headers_tino_user
    ):
        """내 스토리 목록 조회 성공"""
        from datetime import datetime, timedelta
        
        # 스토리 생성
        deadline = (datetime.now() + timedelta(days=7)).isoformat()
        client.post(
            "/tinostory",
            json={
                "title": "내 스토리 목록 테스트",
                "content": "내 스토리 목록 테스트용입니다.",
                "recruitment_type": "PROJECT",
                "deadline": deadline,
                "open_chat_link": "https://open.kakao.com/test"
            },
            headers=auth_headers_tino_user
        )
        
        # 내 스토리 조회
        response = client.get("/mypage/stories", headers=auth_headers_tino_user)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "stories" in data
        assert "total" in data
        assert data["total"] >= 1
        
        story = data["stories"][0]
        assert "id" in story
        assert "title" in story
        assert "recruitment_type" in story
        assert "recruitment_status" in story
        assert "days_until_deadline" in story
    
    def test_my_stories_with_status_filter(
        self, client, auth_headers_tino_user
    ):
        """내 스토리 - 상태 필터 테스트"""
        response = client.get(
            "/mypage/stories?status_filter=recruiting",
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # 모든 스토리가 모집중인지 확인
        for story in data["stories"]:
            assert story["recruitment_status"] == "RECRUITING"
    
    def test_profile_update_nickname(
        self, client, auth_headers_tino_user
    ):
        """프로필 수정 - 닉네임 변경"""
        response = client.put(
            "/mypage/profile",
            json={"nickname": "새닉네임123"},
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["nickname"] == "새닉네임123"
    
    def test_profile_update_grade(
        self, client, auth_headers_tino_user
    ):
        """프로필 수정 - 학년 변경"""
        response = client.put(
            "/mypage/profile",
            json={"grade": 4},
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert data["grade"] == 4
    
    def test_profile_update_nickname_duplicate(
        self, client, auth_headers_tino_user, second_user
    ):
        """프로필 수정 - 중복 닉네임 실패"""
        response = client.put(
            "/mypage/profile",
            json={"nickname": second_user.nickname},
            headers=auth_headers_tino_user
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
