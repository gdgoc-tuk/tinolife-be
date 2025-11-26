"""
Users API Integration Tests
사용자 관련 API 엔드포인트의 통합 테스트
"""

from fastapi import status


class TestUsersAPI:
    """사용자 API 테스트"""

    def test_check_nickname_available(self, client):
        """사용 가능한 닉네임 확인 테스트"""
        response = client.get("/users/check-nickname?nickname=새로운닉네임")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["available"] is True
        assert "사용 가능" in data["message"]

    def test_check_nickname_unavailable(self, client, sample_user):
        """이미 사용 중인 닉네임 확인 테스트"""
        response = client.get(f"/users/check-nickname?nickname={sample_user.nickname}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["available"] is False
        assert "이미 사용" in data["message"]

    def test_check_nickname_invalid_length(self, client):
        """잘못된 길이의 닉네임 확인 테스트"""
        # 너무 짧은 닉네임
        response = client.get("/users/check-nickname?nickname=a")
        assert response.status_code == 422

        # 너무 긴 닉네임
        response = client.get("/users/check-nickname?nickname=" + "a" * 21)
        assert response.status_code == 422

    def test_get_users_list(self, client, sample_user):
        """사용자 목록 조회 테스트"""
        response = client.get("/users/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert any(user["email"] == sample_user.email for user in data)

    def test_get_users_with_pagination(self, client, db_session, sample_major):
        """페이지네이션이 적용된 사용자 목록 조회 테스트"""
        from app.domains.users.model import User
        from app.common.security import hash_password

        # 여러 사용자 생성
        for i in range(5):
            user = User(
                email=f"user{i}@test.ac.kr",
                nickname=f"사용자{i}",
                student_id=f"2021000{i}",
                hashed_password=hash_password("password123"),
                grade=2,
                major_id=sample_major.id,
                is_active=True,
                is_email_verified=True,
            )
            db_session.add(user)
        db_session.commit()

        # 첫 2개만 조회
        response = client.get("/users/?skip=0&limit=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2

    def test_get_user_by_id(self, client, sample_user):
        """특정 사용자 조회 테스트"""
        response = client.get(f"/users/{sample_user.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_user.id
        assert data["email"] == sample_user.email
        assert data["nickname"] == sample_user.nickname
        # grade, major_id는 응답 스키마에 따라 있을 수도 있고 없을 수도 있음

    def test_get_nonexistent_user(self, client):
        """존재하지 않는 사용자 조회 테스트"""
        response = client.get("/users/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_user(self, client, sample_user, auth_headers):
        """사용자 삭제 (소프트 삭제) 테스트"""
        response = client.delete(f"/users/{sample_user.id}", headers=auth_headers)

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 삭제 후 조회 시 비활성 상태 확인
        get_response = client.get(f"/users/{sample_user.id}")
        # 소프트 삭제된 경우 여전히 조회 가능하지만 is_active=False
        if get_response.status_code == status.HTTP_200_OK:
            assert get_response.json()["is_active"] is False
