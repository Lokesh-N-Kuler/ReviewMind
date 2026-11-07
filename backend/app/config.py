import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "reviewmind.db").as_posix()

class Settings(BaseSettings):
    APP_NAME: str = "ReviewMind"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = True

    # Database: Supports PostgreSQL or SQLite for local dev
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH}"

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v.startswith("sqlite:///./"):
            rel_part = v[len("sqlite:///./"):]
            abs_path = (BASE_DIR / rel_part).resolve()
            return f"sqlite:///{abs_path.as_posix()}"
        return v

    # Security & Auth
    JWT_SECRET_KEY: str = "reviewmind-secure-production-jwt-key-32chars-min-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Groq AI Service
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "openai/gpt-oss-20b"
    GROQ_TIMEOUT_SECONDS: int = 60

    # Hindsight Persistent Agent Memory
    HINDSIGHT_BASE_URL: str = "https://api.hindsight.vectorize.io"
    HINDSIGHT_API_KEY: Optional[str] = None
    HINDSIGHT_BANK_ID: str = "reviewmind"
    HINDSIGHT_TIMEOUT_SECONDS: int = 60

    # GitHub OAuth & Integration
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_REDIRECT_URI: str = "http://localhost:3000/github/callback"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=(str(BASE_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
