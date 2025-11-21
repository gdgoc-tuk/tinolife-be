from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from app.core.config import settings

# Base 클래스 - 모든 모델이 상속받음
Base = declarative_base()

# 동기 엔진 (Alembic 마이그레이션용)
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 동기 세션
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# 비동기 엔진 (FastAPI용)
async_engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# 비동기 세션
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# 동기 DB 세션 의존성 (Alembic용)
def get_db():
    """동기 데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 비동기 DB 세션 의존성 (FastAPI용)
async def get_async_db():
    """비동기 데이터베이스 세션 생성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# 데이터베이스 초기화
def init_db():
    """데이터베이스 테이블 생성 (개발용)"""
    Base.metadata.create_all(bind=engine)


# 데이터베이스 테이블 삭제
def drop_db():
    """데이터베이스 테이블 삭제 (개발용)"""
    Base.metadata.drop_all(bind=engine)
