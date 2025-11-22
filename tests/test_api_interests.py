"""
Interests API Integration Tests
관심사 관련 API 엔드포인트의 통합 테스트
"""

from fastapi import status


class TestInterestsAPI:
    """관심사 API 테스트"""

    def test_get_interests_list(self, client, sample_interest):
        """관심사 목록 조회 테스트"""
        response = client.get("/interests/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert len(data["items"]) > 0
        assert any(
            interest["name"] == sample_interest.name for interest in data["items"]
        )

    def test_get_interests_with_pagination(self, client, db_session):
        """페이지네이션이 적용된 관심사 목록 조회 테스트"""
        from app.domains.interests.model import Interest

        # 여러 관심사 생성
        interests = []
        for i in range(25):
            interest = Interest(name=f"관심사{i}", is_active=True)
            interests.append(interest)

        db_session.add_all(interests)
        db_session.commit()

        # 첫 페이지 조회 (기본 20개)
        response = client.get("/interests/?page=1&size=20")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["items"]) == 20
        assert data["page"] == 1
        assert data["size"] == 20
        assert data["total"] >= 25
        assert data["total_pages"] >= 2

        # 두 번째 페이지 조회
        response = client.get("/interests/?page=2&size=20")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 2

    def test_get_interests_active_only(self, client, db_session):
        """활성화된 관심사만 조회 테스트"""
        from app.domains.interests.model import Interest

        # 활성 관심사
        active_interest = Interest(name="활성관심사", is_active=True)
        # 비활성 관심사
        inactive_interest = Interest(name="비활성관심사", is_active=False)

        db_session.add_all([active_interest, inactive_interest])
        db_session.commit()

        # 활성 관심사만 조회
        response = client.get("/interests/?active_only=true")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(interest["is_active"] for interest in data["items"])
        assert any(interest["name"] == "활성관심사" for interest in data["items"])
        assert not any(interest["name"] == "비활성관심사" for interest in data["items"])

    def test_get_interests_all(self, client, db_session):
        """모든 관심사 조회 테스트 (비활성 포함)"""
        from app.domains.interests.model import Interest

        # 활성 관심사
        active_interest = Interest(name="활성관심사2", is_active=True)
        # 비활성 관심사
        inactive_interest = Interest(name="비활성관심사2", is_active=False)

        db_session.add_all([active_interest, inactive_interest])
        db_session.commit()

        # 모든 관심사 조회
        response = client.get("/interests/?active_only=false")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(interest["name"] == "활성관심사2" for interest in data["items"])
        assert any(interest["name"] == "비활성관심사2" for interest in data["items"])

    def test_get_interest_by_id(self, client, sample_interest):
        """특정 관심사 조회 테스트"""
        response = client.get(f"/interests/{sample_interest.id}")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_interest.id
        assert data["name"] == sample_interest.name

    def test_get_nonexistent_interest(self, client):
        """존재하지 않는 관심사 조회 테스트"""
        response = client.get("/interests/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_interest(self, client):
        """새 관심사 생성 테스트"""
        response = client.post("/interests/", json={"name": "신규관심사"})

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "신규관심사"
        assert data["is_active"] is True
        assert "id" in data

    def test_create_duplicate_interest(self, client, sample_interest):
        """중복 관심사 생성 시도 테스트"""
        response = client.post("/interests/", json={"name": sample_interest.name})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_interest(self, client, sample_interest):
        """관심사 정보 업데이트 테스트"""
        response = client.put(
            f"/interests/{sample_interest.id}", json={"name": "변경된관심사명"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "변경된관심사명"

    def test_update_interest_deactivate(self, client, sample_interest):
        """관심사 비활성화 테스트"""
        response = client.put(
            f"/interests/{sample_interest.id}", json={"is_active": False}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False

    def test_update_nonexistent_interest(self, client):
        """존재하지 않는 관심사 업데이트 시도 테스트"""
        response = client.put("/interests/99999", json={"name": "업데이트실패"})

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_interest(self, client, db_session):
        """관심사 삭제 (소프트 삭제) 테스트"""
        from app.domains.interests.model import Interest

        interest = Interest(name="삭제될관심사", is_active=True)
        db_session.add(interest)
        db_session.commit()
        db_session.refresh(interest)

        response = client.delete(f"/interests/{interest.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # 삭제 후 조회 시 비활성 상태 확인
        get_response = client.get(f"/interests/{interest.id}")
        if get_response.status_code == status.HTTP_200_OK:
            assert get_response.json()["is_active"] is False

    def test_delete_nonexistent_interest(self, client):
        """존재하지 않는 관심사 삭제 시도 테스트"""
        response = client.delete("/interests/99999")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_pagination_invalid_page(self, client):
        """잘못된 페이지 번호로 조회 시도 테스트"""
        # 0 이하의 페이지
        response = client.get("/interests/?page=0")
        assert response.status_code == 422

        # 음수 페이지
        response = client.get("/interests/?page=-1")
        assert response.status_code == 422

    def test_pagination_invalid_size(self, client):
        """잘못된 페이지 크기로 조회 시도 테스트"""
        # 0 이하의 크기
        response = client.get("/interests/?size=0")
        assert response.status_code == 422

        # 최대값 초과
        response = client.get("/interests/?size=101")
        assert response.status_code == 422
