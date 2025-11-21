#!/usr/bin/env python3
"""
통합 초기 데이터 시딩 스크립트

애플리케이션에 필요한 모든 초기 데이터를 삽입합니다.
- 허용된 이메일 도메인
- 기타 필수 마스터 데이터
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.domains.auth.model import AllowedEmailDomain


def seed_allowed_domains(db):
    """허용된 이메일 도메인 초기 데이터 삽입"""
    print("📧 허용 이메일 도메인 시딩 중...")
    
    # 초기 허용 도메인 목록
    initial_domains = [
        {
            "domain": "@tukorea.ac.kr",
            "university_name": "한국공학대학교",
        },
    ]
    
    added_count = 0
    skipped_count = 0
    
    for domain_data in initial_domains:
        # 이미 존재하는지 확인
        existing = db.query(AllowedEmailDomain).filter(
            AllowedEmailDomain.domain == domain_data["domain"]
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # 새 도메인 추가
        new_domain = AllowedEmailDomain(**domain_data)
        db.add(new_domain)
        added_count += 1
    
    if added_count > 0:
        db.commit()
        print(f"   ✅ {added_count}개 도메인 추가됨")
    else:
        print(f"   ⏭️  모든 도메인 이미 존재 ({skipped_count}개)")
    
    return added_count, skipped_count


def seed_all():
    """모든 초기 데이터 삽입"""
    print("="*60)
    print("🌱 초기 데이터 시딩 시작...")
    print("="*60 + "\n")
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        total_added = 0
        total_skipped = 0
        
        # 1. 허용 이메일 도메인
        added, skipped = seed_allowed_domains(db)
        total_added += added
        total_skipped += skipped
        
        # 2. 여기에 다른 시드 함수 추가
        # added, skipped = seed_majors(db)
        # total_added += added
        # total_skipped += skipped
        
        print("\n" + "="*60)
        print("✨ 시딩 완료!")
        print(f"   📊 총 추가됨: {total_added}개")
        print(f"   📊 총 건너뜀: {total_skipped}개")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        seed_all()
        sys.exit(0)
    except Exception:
        sys.exit(1)
