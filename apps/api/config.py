from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_VERSION: str = "0.1.0"
    ENV: str = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Auth — RS256 keypair
    JWT_PRIVATE_KEY: str = ""
    JWT_PUBLIC_KEY: str = ""
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"]

    # AWS
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET_NAME: str = "orchestragrant-documents"
    SES_FROM_ADDRESS: str = "noreply@orchestragrant.com"
    S3_PRESIGNED_EXPIRY_SECONDS: int = 900  # 15 minutes

    # AI
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLAMAPARSE_API_KEY: str = ""

    # External APIs
    GRANTS_GOV_API_KEY: str = ""
    CANDID_CLIENT_ID: str = ""
    CANDID_CLIENT_SECRET: str = ""

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""

    # App
    APP_BASE_URL: str = "https://app.orchestragrant.com"

    # Sentry
    SENTRY_DSN: str = ""

    # Rate limiting
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 10
    RATE_LIMIT_LOGIN_LOCKOUT_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_LOCKOUT_MINUTES: int = 15


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
