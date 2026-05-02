from functools import lru_cache
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    DATABASE_URL: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    LLAMAPARSE_API_KEY: str = ""

    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS: int = 3072
    GENERATION_MODEL: str = "gpt-4o"
    FALLBACK_MODEL: str = "claude-3-5-sonnet-20241022"

    RAG_TOP_K: int = 8
    RAG_MIN_SIMILARITY: float = 0.72

    SENTRY_DSN: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
