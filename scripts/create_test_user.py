"""
테스트 사용자 생성 스크립트
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.common.security import hash_password

# 모든 모델 임포트
from app.domains.users.model import User
from app.domains.majors.model import Major
from app.domains.interests.model import Interest, user_interests
from app.domains.qna.model import Category, Tag, Question, Answer, question_tags


def create_test_user():
    """테스트 사용자 생성"""
    db: Session = SessionLocal()

    try:
        # 기존 테스트 사용자 확인
        existing = db.query(User).filter(User.email == "test@tukorea.ac.kr").first()
        if existing:
            print("✅ 테스트 사용자가 이미 존재합니다.")
            print(f"   - Email: test@tukorea.ac.kr")
            print(f"   - Nickname: {existing.nickname}")
            print(f"   - ID: {existing.id}")
            return

        # 첫 번째 전공 찾기
        major = db.query(Major).first()
        if not major:
            print("❌ 전공 데이터가 없습니다. seed_initial_data.py를 먼저 실행하세요.")
            return

        # 테스트 사용자 생성
        test_user = User(
            email="test@tukorea.ac.kr",
            hashed_password=hash_password("Test1234!"),
            nickname="테스트유저",
            student_id="2020000001",
            grade=3,
            major_id=major.id,
            is_active=True,
            is_email_verified=True,
        )

        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print("✅ 테스트 사용자가 생성되었습니다!")
        print(f"   - Email: test@tukorea.ac.kr")
        print(f"   - Password: Test1234!")
        print(f"   - Nickname: {test_user.nickname}")
        print(f"   - ID: {test_user.id}")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_user()
