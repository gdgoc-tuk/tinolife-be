"""
E2E 통합 테스트 - 전체 사용자 시나리오 검증
회원가입 → 로그인 → 질문 등록 → 답변 → 바운티 → 채택 플로우를 검증합니다.
"""

import pytest
from fastapi import status


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
        """질문 상세 조회"""
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
        
        # 상세 조회
        response = client.get(f"/qna/questions/{question_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == question_id
        assert data["title"] == "상세 조회용 질문"
        assert data["view_count"] >= 1  # 조회 시 조회수 증가


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
        
        # 질문 상태 확인
        question_detail = client.get(f"/qna/questions/{question_id}")
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
