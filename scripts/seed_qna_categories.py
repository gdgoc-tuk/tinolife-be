"""
QnA 초기 카테고리 데이터 시딩
"""
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

# 모든 모델 임포트 (SQLAlchemy relationship 설정을 위해 필요)
from app.domains.users.model import User
from app.domains.majors.model import Major
from app.domains.interests.model import Interest, user_interests
from app.domains.qna.model import (
    Category, Tag, Question, Answer, question_tags
)


def seed_categories():
    """초기 카테고리 데이터 생성"""
    db: Session = SessionLocal()

    try:
        # 기존 카테고리 확인
        existing_count = db.query(Category).count()
        if existing_count > 0:
            print(f"✅ 이미 카테고리 {existing_count}개가 존재합니다.")
            return

        # 초기 카테고리
        categories = [
            {"name": "학교생활", "display_order": 1},
            {"name": "전공/학업", "display_order": 2},
            {"name": "진로/취업", "display_order": 3},
            {"name": "인간관계", "display_order": 4},
            {"name": "기타", "display_order": 5},
        ]

        for cat_data in categories:
            category = Category(**cat_data)
            db.add(category)

        db.commit()
        print(f"✅ 카테고리 {len(categories)}개가 생성되었습니다.")

        # 생성된 카테고리 출력
        for cat in categories:
            print(f"   - {cat['name']} (순서: {cat['display_order']})")

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    seed_categories()
