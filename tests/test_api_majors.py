"""
Majors API Integration Tests
전공 관련 API 엔드포인트의 통합 테스트
"""
import pytest
from fastapi import status


class TestMajorsAPI:
    """전공 API 테스트"""
    
    def test_get_majors_list(self, client, sample_major):
        """전공 목록 조회 테스트"""
        response = client.get("/majors/")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0
        assert any(major["name"] == sample_major.name for major in data)
    
    def test_get_majors_active_only(self, client, db_session):
        """활성화된 전공만 조회 테스트"""
        from app.domains.majors.model import Major
        
        # 활성 전공
        active_major = Major(name="활성전공", code="ACT", is_active=True)
        # 비활성 전공
        inactive_major = Major(name="비활성전공", code="INA", is_active=False)
        
        db_session.add_all([active_major, inactive_major])
        db_session.commit()
        
        # 활성 전공만 조회
        response = client.get("/majors/?active_only=true")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert all(major["is_active"] for major in data)
        assert any(major["name"] == "활성전공" for major in data)
        assert not any(major["name"] == "비활성전공" for major in data)
    
    def test_get_majors_all(self, client, db_session):
        """모든 전공 조회 테스트 (비활성 포함)"""
        from app.domains.majors.model import Major
        
        # 활성 전공
        active_major = Major(name="활성전공2", code="ACT2", is_active=True)
        # 비활성 전공
        inactive_major = Major(name="비활성전공2", code="INA2", is_active=False)
        
        db_session.add_all([active_major, inactive_major])
        db_session.commit()
        
        # 모든 전공 조회
        response = client.get("/majors/?active_only=false")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert any(major["name"] == "활성전공2" for major in data)
        assert any(major["name"] == "비활성전공2" for major in data)
    
    def test_get_major_by_id(self, client, sample_major):
        """특정 전공 조회 테스트"""
        response = client.get(f"/majors/{sample_major.id}")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_major.id
        assert data["name"] == sample_major.name
        assert data["code"] == sample_major.code
    
    def test_get_nonexistent_major(self, client):
        """존재하지 않는 전공 조회 테스트"""
        response = client.get("/majors/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_create_major(self, client):
        """새 전공 생성 테스트"""
        response = client.post(
            "/majors/",
            json={
                "name": "신규전공",
                "code": "NEW"
            }
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "신규전공"
        assert data["code"] == "NEW"
        assert data["is_active"] is True
        assert "id" in data
    
    def test_create_major_without_code(self, client):
        """코드 없이 전공 생성 테스트"""
        response = client.post(
            "/majors/",
            json={"name": "코드없는전공"}
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "코드없는전공"
        assert data["code"] is None
    
    def test_create_duplicate_major(self, client, sample_major):
        """중복 전공 생성 시도 테스트"""
        response = client.post(
            "/majors/",
            json={
                "name": sample_major.name,
                "code": "DUP"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_update_major(self, client, sample_major):
        """전공 정보 업데이트 테스트"""
        response = client.put(
            f"/majors/{sample_major.id}",
            json={
                "name": "변경된전공명",
                "code": "CHG"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "변경된전공명"
        assert data["code"] == "CHG"
    
    def test_update_major_deactivate(self, client, sample_major):
        """전공 비활성화 테스트"""
        response = client.put(
            f"/majors/{sample_major.id}",
            json={"is_active": False}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["is_active"] is False
    
    def test_update_nonexistent_major(self, client):
        """존재하지 않는 전공 업데이트 시도 테스트"""
        response = client.put(
            "/majors/99999",
            json={"name": "업데이트실패"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
    
    def test_delete_major(self, client, db_session):
        """전공 삭제 (소프트 삭제) 테스트"""
        from app.domains.majors.model import Major
        
        major = Major(name="삭제될전공", code="DEL", is_active=True)
        db_session.add(major)
        db_session.commit()
        db_session.refresh(major)
        
        response = client.delete(f"/majors/{major.id}")
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 삭제 후 조회 시 비활성 상태 확인
        get_response = client.get(f"/majors/{major.id}")
        if get_response.status_code == status.HTTP_200_OK:
            assert get_response.json()["is_active"] is False
    
    def test_delete_nonexistent_major(self, client):
        """존재하지 않는 전공 삭제 시도 테스트"""
        response = client.delete("/majors/99999")
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
