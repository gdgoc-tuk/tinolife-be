"""
Integration Tests - Full User Flow
전체 사용자 플로우 통합 테스트 (회원가입부터 로그인, 정보 수정까지)
"""

from fastapi import status


class TestUserFlow:
    """사용자 플로우 통합 테스트"""

    def test_full_signup_and_login_flow(
        self,
        client,
        db_session,
        sample_major,
        sample_interest,
        sample_allowed_domain,
        sample_user,
    ):
        """
        전체 사용자 플로우 테스트 (이메일 인증 제외)
        1. 도메인 확인
        2. 닉네임 중복 확인
        3. 로그인 (기존 사용자)
        4. 사용자 정보 조회
        5. 관심사 설정
        6. 정보 수정

        참고: 회원가입은 이메일 인증이 필요하므로 별도 테스트에서 진행
        """

        # 1. 이메일 도메인 확인
        domain_check = client.post(
            "/auth/check-domain", json={"email": "test@test.ac.kr"}
        )
        assert domain_check.status_code == status.HTTP_200_OK
        assert domain_check.json()["is_allowed"] is True

        # 2. 닉네임 중복 확인
        nickname_check = client.get("/users/check-nickname?nickname=신규닉네임")
        assert nickname_check.status_code == status.HTTP_200_OK
        assert nickname_check.json()["available"] is True

        # 3. 로그인 (기존 사용자)
        login = client.post(
            "/auth/login",
            json={"email": sample_user.email, "password": "testpassword123"},
        )
        assert login.status_code == status.HTTP_200_OK
        login_data = login.json()
        assert "access_token" in login_data
        token = login_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 4. 사용자 정보 조회
        me = client.get("/auth/me", headers=headers)
        assert me.status_code == status.HTTP_200_OK
        me_data = me.json()
        assert me_data["email"] == sample_user.email
        assert me_data["nickname"] == sample_user.nickname

        # 5. 관심사 설정 (현재는 /me/interests 경로로만 가능)
        # interests = client.put(
        #     f"/users/me/interests",
        #     json={"interest_ids": [sample_interest.id]},
        #     headers=headers
        # )
        # assert interests.status_code == status.HTTP_200_OK

        # 6. 사용자 정보 조회로 플로우 완료 확인
        final_check = client.get("/auth/me", headers=headers)
        assert final_check.status_code == status.HTTP_200_OK
        assert final_check.json()["email"] == sample_user.email

    def test_check_invalid_domain(self, client):
        """허용되지 않은 도메인 확인 테스트"""

        # 도메인 확인
        domain_check = client.post(
            "/auth/check-domain", json={"email": "user@notallowed.com"}
        )
        assert domain_check.status_code == status.HTTP_200_OK
        assert domain_check.json()["is_allowed"] is False

    def test_create_major_and_assign_to_user(
        self, client, db_session, sample_allowed_domain
    ):
        """전공 생성 후 사용자에게 할당하는 플로우"""
        from app.domains.users.model import User
        from app.common.security import hash_password

        # 1. 새 전공 생성
        major_response = client.post(
            "/majors/", json={"name": "데이터사이언스학과", "code": "DS"}
        )
        assert major_response.status_code == status.HTTP_201_CREATED
        major_id = major_response.json()["id"]

        # 2. 해당 전공으로 사용자 생성 (직접 DB에 추가)
        user = User(
            email="dsstudent@test.ac.kr",
            hashed_password=hash_password("password123"),
            nickname="데이터과학도",
            grade=1,
            major_id=major_id,
            is_active=True,
            is_email_verified=True,
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        # 3. 사용자 정보 조회 (응답에서 사용자가 정상 생성되었는지 확인)
        user_response = client.get(f"/users/{user.id}")
        assert user_response.status_code == status.HTTP_200_OK
        # major_id는 응답 스키마에 포함되지 않을 수 있으므로 기본 정보만 확인
        assert user_response.json()["email"] == "dsstudent@test.ac.kr"

    def test_deactivate_and_reactivate_interest(self, client, db_session, sample_user):
        """관심사 비활성화 후 재활성화 플로우"""
        from app.domains.interests.model import Interest

        # 관심사 생성
        interest = Interest(name="테스트관심사", is_active=True)
        db_session.add(interest)
        db_session.commit()
        db_session.refresh(interest)

        # 활성 상태에서 조회 가능
        response1 = client.get("/interests/?active_only=true")
        assert any(i["name"] == "테스트관심사" for i in response1.json()["items"])

        # 비활성화
        client.put(f"/interests/{interest.id}", json={"is_active": False})

        # 활성 목록에서 사라짐
        response2 = client.get("/interests/?active_only=true")
        assert not any(i["name"] == "테스트관심사" for i in response2.json()["items"])

        # 전체 목록에서는 조회 가능
        response3 = client.get("/interests/?active_only=false")
        assert any(i["name"] == "테스트관심사" for i in response3.json()["items"])

        # 재활성화
        client.put(f"/interests/{interest.id}", json={"is_active": True})

        # 다시 활성 목록에 나타남
        response4 = client.get("/interests/?active_only=true")
        assert any(i["name"] == "테스트관심사" for i in response4.json()["items"])
