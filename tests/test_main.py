import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """테스트 클라이언트 픽스처"""
    return TestClient(app)


def test_root(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["message"] == "Welcome to TinoLife API"


def test_health_check(client):
    """헬스 체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
