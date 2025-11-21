from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


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
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # 데이터베이스 설정 (추후 사용)
    DATABASE_URL: str = ""
    
    # JWT 설정 (추후 사용)
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()
