from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.users.schema import UserCreate, UserResponse, SignupRequest
from app.domains.users.model import User
from app.domains.interests.model import Interest, user_interests
from app.common.security import hash_password, verify_password
from app.common.exceptions import BadRequestException, NotFoundException


class UserService:
    """사용자 비즈니스 로직을 처리하는 서비스"""

    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """ID로 사용자 조회"""
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_nickname(self, db: Session, nickname: str) -> Optional[User]:
        """닉네임으로 사용자 조회 (대소문자 구분 없음)"""
        return db.query(User).filter(
            func.lower(User.nickname) == func.lower(nickname)
        ).first()
    
    def check_nickname_availability(self, db: Session, nickname: str) -> bool:
        """
        닉네임 사용 가능 여부 확인
        
        Args:
            db: 데이터베이스 세션
            nickname: 확인할 닉네임
            
        Returns:
            bool: 사용 가능하면 True, 이미 존재하면 False
        """
        existing_user = self.get_user_by_nickname(db, nickname)
        return existing_user is None

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """사용자 목록 조회"""
        return db.query(User).offset(skip).limit(limit).all()

    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """
        사용자 생성 (내부용)
        
        Args:
            db: 데이터베이스 세션
            user_data: 사용자 생성 데이터 (hashed_password 포함)
            
        Returns:
            User: 생성된 사용자
        """
        user = User(
            email=user_data.email,
            hashed_password=user_data.hashed_password,
            nickname=user_data.nickname,
            grade=user_data.grade,
            major_id=user_data.major_id,
            is_email_verified=user_data.is_email_verified,
            privacy_policy_agreed_at=datetime.now(timezone.utc)
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def signup(
        self, 
        db: Session, 
        signup_data: SignupRequest
    ) -> User:
        """
        회원가입 처리
        
        Args:
            db: 데이터베이스 세션
            signup_data: 회원가입 요청 데이터
            
        Returns:
            User: 생성된 사용자
            
        Raises:
            BadRequestException: 이메일 중복, 개인정보 동의 미체크 등
        """
        # 1. 개인정보 처리방침 동의 확인
        if not signup_data.privacy_policy_agreed:
            raise BadRequestException("개인정보 처리방침에 동의해야 합니다.")
        
        # 2. 이메일 중복 체크
        existing_user = self.get_user_by_email(db, signup_data.email)
        if existing_user:
            raise BadRequestException("이미 가입된 이메일입니다.")
        
        # 3. 닉네임 중복 체크
        if not self.check_nickname_availability(db, signup_data.nickname):
            raise BadRequestException("이미 사용 중인 닉네임입니다.")
        
        # 4. 비밀번호 해싱
        hashed_password = hash_password(signup_data.password)
        
        # 5. 사용자 생성 데이터 준비
        user_create = UserCreate(
            email=signup_data.email,
            hashed_password=hashed_password,
            nickname=signup_data.nickname,
            grade=signup_data.grade,
            major_id=signup_data.major_id,
            is_email_verified=True  # 이메일 인증 완료 상태로 가정
        )
        
        # 6. 사용자 생성
        user = self.create_user(db, user_create)
        
        # 7. 관심사 연결 (선택적)
        if signup_data.interest_ids:
            self.add_user_interests(db, user.id, signup_data.interest_ids)
        
        return user
    
    def add_user_interests(
        self, 
        db: Session, 
        user_id: int, 
        interest_ids: List[int]
    ) -> None:
        """
        사용자 관심사 추가
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            interest_ids: 관심사 ID 목록
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("사용자를 찾을 수 없습니다.")
        
        # 관심사 존재 여부 확인
        interests = db.query(Interest).filter(Interest.id.in_(interest_ids)).all()
        
        if len(interests) != len(interest_ids):
            raise BadRequestException("존재하지 않는 관심사가 포함되어 있습니다.")
        
        # 관심사 연결
        for interest in interests:
            # 중복 체크
            exists = db.query(user_interests).filter(
                user_interests.c.user_id == user_id,
                user_interests.c.interest_id == interest.id
            ).first()
            
            if not exists:
                stmt = user_interests.insert().values(
                    user_id=user_id,
                    interest_id=interest.id
                )
                db.execute(stmt)
        
        db.commit()
    
    def update_user_interests(
        self, 
        db: Session, 
        user_id: int, 
        interest_ids: List[int]
    ) -> None:
        """
        사용자 관심사 업데이트 (기존 관심사 제거 후 새로 추가)
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            interest_ids: 새로운 관심사 ID 목록
        """
        user = self.get_user_by_id(db, user_id)
        if not user:
            raise NotFoundException("사용자를 찾을 수 없습니다.")
        
        # 관심사 존재 여부 확인
        interests = db.query(Interest).filter(Interest.id.in_(interest_ids)).all()
        
        if len(interests) != len(interest_ids):
            raise BadRequestException("존재하지 않는 관심사가 포함되어 있습니다.")
        
        # 1. 기존 관심사 모두 제거
        db.execute(
            user_interests.delete().where(user_interests.c.user_id == user_id)
        )
        
        # 2. 새 관심사 추가
        for interest_id in interest_ids:
            stmt = user_interests.insert().values(
                user_id=user_id,
                interest_id=interest_id
            )
            db.execute(stmt)
        
        db.commit()

    def update_user(self, db: Session, user_id: int, user_data: dict) -> Optional[User]:
        """사용자 정보 업데이트"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return None
        
        for field, value in user_data.items():
            if hasattr(user, field):
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        return user

    def delete_user(self, db: Session, user_id: int) -> bool:
        """사용자 삭제 (소프트 삭제)"""
        user = self.get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.is_active = False
        db.commit()
        return True
    
    def verify_user_password(self, db: Session, email: str, password: str) -> Optional[User]:
        """
        사용자 비밀번호 검증 (로그인용)
        
        Args:
            db: 데이터베이스 세션
            email: 이메일
            password: 평문 비밀번호
            
        Returns:
            User: 인증 성공 시 사용자 객체, 실패 시 None
        """
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user


def get_user_service() -> UserService:
    """UserService 의존성 주입"""
    return UserService()
