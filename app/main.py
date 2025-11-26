from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.common.exceptions import http_exception_handler, general_exception_handler

# 도메인 라우터 import
from app.domains.users.router import router as users_router
from app.domains.auth.router import router as auth_router
from app.domains.majors.router import router as majors_router
from app.domains.interests.router import router as interests_router
from app.domains.qna.router import router as qna_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 수명 주기 관리

    startup: 애플리케이션 시작 시 실행
    shutdown: 애플리케이션 종료 시 실행

    주의: 개발 모드에서 리로드 시마다 실행될 수 있습니다.
    실제 초기 데이터는 entrypoint.sh에서 처리하며,
    여기서는 데이터 확인만 수행합니다.
    """
    # Startup
    # 모든 모델 임포트 (SQLAlchemy relationship 설정을 위해 필요)
    from app.domains.users.model import User
    from app.domains.users.tino_transaction import TinoTransaction, TransactionType
    from app.domains.auth.model import AllowedEmailDomain, RefreshToken, LoginHistory, EmailVerification
    from app.domains.majors.model import Major
    from app.domains.interests.model import Interest, user_interests
    from app.domains.qna.model import (
        Category, Tag, Question, Answer, AnswerVote, AnswerComment,
        QuestionInterest, QuestionBookmark, QuestionImage, AnswerImage, question_tags
    )

    try:
        engine = create_engine(settings.DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()

        # 허용 도메인 개수 확인
        domain_count = (
            db.query(AllowedEmailDomain)
            .filter(AllowedEmailDomain.is_active.is_(True))
            .count()
        )

        if domain_count == 0:
            print("⚠️  경고: 허용된 이메일 도메인이 없습니다!")
            print(
                "   scripts/seed_initial_data.py를 실행하여 초기 데이터를 추가하세요."
            )
        else:
            print(f"✅ 허용 이메일 도메인: {domain_count}개 활성화됨")

        db.close()
    except Exception as e:
        print(f"⚠️  Startup 체크 실패: {e}")

    yield  # 애플리케이션 실행

    # Shutdown (필요시 정리 작업)
    print("👋 애플리케이션 종료 중...")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        lifespan=lifespan,  # lifespan 이벤트 핸들러 등록
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 예외 핸들러 등록
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)

    # 도메인 라우터 등록
    app.include_router(users_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(majors_router, prefix="/api/v1")
    app.include_router(interests_router, prefix="/api/v1")
    app.include_router(qna_router, prefix="/api/v1")

    # 정적 파일 서빙 (업로드된 이미지)
    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    # 기본 엔드포인트
    @app.get("/")
    async def root():
        """루트 엔드포인트"""
        return {
            "message": "Welcome to TinoLife API",
            "version": settings.VERSION,
            "docs": "/docs",
        }

    @app.get("/health")
    async def health_check():
        """헬스 체크 엔드포인트"""
        return {"status": "healthy"}

    return app


# 애플리케이션 인스턴스 생성
app = create_app()
