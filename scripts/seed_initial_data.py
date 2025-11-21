#!/usr/bin/env python3
"""
초기 데이터 시딩 스크립트
- 허용된 이메일 도메인
- 전공 데이터
- 관심사 데이터
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.domains.auth.model import AllowedEmailDomain
from app.domains.majors.model import Major
from app.domains.users.model import User
from app.domains.interests.model import Interest  # 모델 관계를 위해 필요


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


def seed_majors(db):
    """전공 데이터 시딩 (운영자 설정 기본값)"""
    print("🎓 전공 데이터 시딩 중...")
    
    # 운영자가 설정한 기본 전공 목록
    default_majors = [
        "게임공학과",
        "컴퓨터공학과",
        "소프트웨어학과",
        "인공지능학과",
        "IT반도체융합대학 자율전공",
        "전자공학전공",
        "임베디드시스템전공",
        "나노반도체공학전공",
        "반도체시스템전공",
        "스마트기계융합대학 자율전공",
        "기계공학과",
        "기계설계전공",
        "지능형모빌리티전공",
        "메카트로닉스전공",
        "AI로봇전공",
        "첨단융합대학 자율전공",
        "신소재공학과",
        "생명화학공학과",
        "전력응용시스템전공",
        "미래에너지시스템전공",
        "경영학전공",
        "IT경영전공",
        "데이터사이언스경영전공",
        "산업디자인공학전공",
        "미디어디자인공학전공",
        "지식융합학부"
    ]
    
    # 데이터베이스에 저장
    added_count = 0
    skipped_count = 0
    
    for major_name in default_majors:
        # 이미 존재하는지 확인
        existing = db.query(Major).filter(
            Major.name == major_name
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # 새 전공 추가
        new_major = Major(
            name=major_name,
            is_active=True
        )
        db.add(new_major)
        added_count += 1
    
    # 커밋
    if added_count > 0:
        db.commit()
        print(f"   ✅ {added_count}개 전공 추가됨")
    
    if skipped_count > 0:
        print(f"   ⏭️  {skipped_count}개 전공 이미 존재")
    
    return added_count, skipped_count


def seed_interests(db):
    """관심사 데이터 시딩 (운영자 설정 기본값)"""
    print("🏷️  관심사 데이터 시딩 중...")
    
    # 운영자가 설정한 기본 관심사 목록
    default_interests = [
        # 전공
        "코딩",
        "AI",
        "데이터 분석",
        "반도체",
        "로봇",
        "기계 설계",
        "UI/UX",
        "미디어 디자인",
        "경영",
        "IT 비즈니스",
        # 활동
        "공모전",
        "해커톤",
        "스타트업",
        "동아리",
        "자격증 준비",
        "연구실 활동",
        "프로젝트 팀",
        "오픈소스",
        "인턴 탐색",
        # 취미
        "음악",
        "여행",
        "운동",
        "게임",
        "독서",
        "테니스",
        "영상 제작",
        "사진",
        "예술"
    ]
    
    # 데이터베이스에 저장
    added_count = 0
    skipped_count = 0
    
    for interest_name in default_interests:
        # 이미 존재하는지 확인
        existing = db.query(Interest).filter(
            Interest.name == interest_name
        ).first()
        
        if existing:
            skipped_count += 1
            continue
        
        # 새 관심사 추가
        new_interest = Interest(
            name=interest_name,
            is_active=True
        )
        db.add(new_interest)
        added_count += 1
    
    # 커밋
    if added_count > 0:
        db.commit()
        print(f"   ✅ {added_count}개 관심사 추가됨")
    
    if skipped_count > 0:
        print(f"   ⏭️  {skipped_count}개 관심사 이미 존재")
    
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
        
        # 2. 전공 데이터
        added, skipped = seed_majors(db)
        total_added += added
        total_skipped += skipped
        
        # 3. 관심사 데이터
        added, skipped = seed_interests(db)
        total_added += added
        total_skipped += skipped
        
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
