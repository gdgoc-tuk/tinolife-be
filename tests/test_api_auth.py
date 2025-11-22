"""
Auth API Integration Tests
인증 관련 API 엔드포인트의 통합 테스트
"""

from fastapi import status


class TestAuthAPI:
    """인증 API 테스트"""

    def test_check_email_domain_allowed(self, client, sample_allowed_domain):
        """허용된 이메일 도메인 확인 테스트"""
        response = client.post(
            "/auth/check-domain", json={"email": "student@test.ac.kr"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_allowed"] is True
        assert data["university_name"] == "테스트대학교"

    def test_check_email_domain_not_allowed(self, client):
        """허용되지 않은 이메일 도메인 확인 테스트"""
        response = client.post(
            "/auth/check-domain", json={"email": "student@notallowed.com"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_allowed"] is False

    def test_get_allowed_domains(self, client, sample_allowed_domain):
        """허용된 도메인 목록 조회 테스트"""
        response = client.get("/auth/allowed-domains")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert data[0]["domain"] == "@test.ac.kr"
        assert data[0]["university_name"] == "테스트대학교"

    def test_create_allowed_domain(self, client):
        """새 허용 도메인 생성 테스트"""
        response = client.post(
            "/auth/allowed-domains",
            json={"domain": "@newuniv.ac.kr", "university_name": "신규대학교"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["domain"] == "@newuniv.ac.kr"
        assert data["university_name"] == "신규대학교"
        assert data["is_active"] is True

    def test_create_duplicate_domain(self, client, sample_allowed_domain):
        """중복 도메인 생성 시 에러 테스트"""
        response = client.post(
            "/auth/allowed-domains",
            json={"domain": "@test.ac.kr", "university_name": "중복대학교"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_allowed_domain(self, client, sample_allowed_domain):
        """허용 도메인 업데이트 테스트"""
        response = client.put(
            f"/auth/allowed-domains/{sample_allowed_domain.id}",
            json={"university_name": "변경된대학교", "is_active": False},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["university_name"] == "변경된대학교"
        assert data["is_active"] is False

    def test_login_success(self, client, sample_user, sample_allowed_domain):
        """로그인 성공 테스트"""
        response = client.post(
            "/auth/login",
            json={"email": "test@test.ac.kr", "password": "testpassword123"},
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user_id" in data  # user 객체 대신 user_id 확인

    def test_login_wrong_password(self, client, sample_user, sample_allowed_domain):
        """잘못된 비밀번호로 로그인 시도 테스트"""
        response = client.post(
            "/auth/login",
            json={"email": "test@test.ac.kr", "password": "wrongpassword"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_nonexistent_user(self, client):
        """존재하지 않는 사용자 로그인 시도 테스트"""
        response = client.post(
            "/auth/login",
            json={"email": "nonexistent@test.ac.kr", "password": "testpassword123"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user(self, client, auth_headers):
        """현재 인증된 사용자 정보 조회 테스트"""
        response = client.get("/auth/me", headers=auth_headers)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@test.ac.kr"
        assert data["nickname"] == "테스트유저"

    def test_get_current_user_without_token(self, client):
        """토큰 없이 사용자 정보 조회 시도 테스트"""
        response = client.get("/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_current_user_invalid_token(self, client):
        """유효하지 않은 토큰으로 사용자 정보 조회 시도 테스트"""
        response = client.get(
            "/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )

        # 유효하지 않은 토큰은 401 Unauthorized 반환
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
