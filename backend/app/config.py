import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "ReviewMind"
    APP_VERSION: str = "1.0.0"
    ENV: str = "development"
    DEBUG: bool = True

    # Database: Supports PostgreSQL or SQLite for local dev
    DATABASE_URL: str = "sqlite:///./reviewmind.db"

    # Security & Auth
    JWT_SECRET_KEY: str = "reviewmind-secure-production-jwt-key-32chars-min-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Groq AI Service
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
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
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
