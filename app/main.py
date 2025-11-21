from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.common.exceptions import http_exception_handler, general_exception_handler

# 도메인 라우터 import
from app.domains.users.router import router as users_router
from app.domains.auth.router import router as auth_router
from app.domains.majors.router import router as majors_router
from app.domains.interests.router import router as interests_router


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
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
