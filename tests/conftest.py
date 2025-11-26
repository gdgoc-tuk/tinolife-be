"""
Test configuration and fixtures
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db

# 모든 모델을 import하여 Base.metadata에 등록
from app.domains.users.model import User  # noqa: F401
from app.domains.users.tino_transaction import TinoTransaction  # noqa: F401
from app.domains.majors.model import Major  # noqa: F401
from app.domains.interests.model import Interest, user_interests  # noqa: F401
from app.domains.auth.model import AllowedEmailDomain, EmailVerification  # noqa: F401
from app.domains.qna.model import (  # noqa: F401
    Category, Tag, Question, Answer, AnswerVote, AnswerComment,
    QuestionInterest, QuestionBookmark, Report
)


# 테스트용 인메모리 데이터베이스 설정
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """테스트용 데이터베이스 세션 생성"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """테스트용 FastAPI 클라이언트 생성"""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app, base_url="http://testserver/api/v1") as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_major(db_session):
    """테스트용 전공 데이터"""
    from app.domains.majors.model import Major

    major = Major(name="컴퓨터공학과", code="CSE", is_active=True)
    db_session.add(major)
    db_session.commit()
    db_session.refresh(major)
    return major


@pytest.fixture
def sample_interest(db_session):
    """테스트용 관심사 데이터"""
    from app.domains.interests.model import Interest

    interest = Interest(name="프로그래밍", is_active=True)
    db_session.add(interest)
    db_session.commit()
    db_session.refresh(interest)
    return interest


@pytest.fixture
def sample_allowed_domain(db_session):
    """테스트용 허용 도메인"""
    from app.domains.auth.model import AllowedEmailDomain

    domain = AllowedEmailDomain(
        domain="@test.ac.kr", university_name="테스트대학교", is_active=True
    )
    db_session.add(domain)
    db_session.commit()
    db_session.refresh(domain)
    return domain


@pytest.fixture
def sample_user(db_session, sample_major):
    """테스트용 사용자 데이터"""
    from app.domains.users.model import User
    from app.common.security import hash_password

    user = User(
        email="test@test.ac.kr",
        nickname="테스트유저",
        student_id="20200001",
        hashed_password=hash_password("testpassword123"),
        grade=3,
        major_id=sample_major.id,
        is_active=True,
        is_email_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, sample_user, sample_allowed_domain):
    """인증된 사용자의 헤더"""
    response = client.post(
        "/auth/login", json={"email": sample_user.email, "password": "testpassword123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
