from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 프로젝트 정보
    PROJECT_NAME: str = "TinoLife API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "TinoLife Backend API"

    # 서버 설정
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False

    # CORS 설정
    ALLOWED_ORIGINS: Union[List[str], str] = ["*"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """CORS origins를 문자열 또는 리스트로 파싱"""
        if isinstance(v, str):
            # 쉼표로 구분된 문자열을 리스트로 변환
            return [origin.strip() for origin in v.split(",")]
        return v

    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/tinolife"
    ASYNC_DATABASE_URL: str = (
        "postgresql+asyncpg://user:password@localhost:5432/tinolife"
    )

    @property
    def sync_database_url(self) -> str:
        """Alembic용 동기 DB URL"""
        return self.DATABASE_URL

    # JWT 설정 (추후 사용)
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # SMTP 설정
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_FROM_NAME: str = "TinoLife"

    # 공공데이터 API 설정
    PUBLIC_DATA_API_KEY: str = ""

    # 이미지 업로드 설정
    UPLOAD_DIR: str = "uploads"  # 로컬 업로드 디렉토리
    MAX_IMAGE_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_IMAGE_TYPES: List[str] = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    
    # S3/MinIO 설정
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_S3_BUCKET: str = "tinolife"
    AWS_S3_REGION: str = "us-east-1"
    AWS_S3_ENDPOINT_URL: str = ""  # MinIO용 (예: http://minio:9000)
    USE_S3: bool = False  # True면 S3/MinIO 사용, False면 로컬 저장

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # .env에 정의되지 않은 필드 무시
    )


settings = Settings()
