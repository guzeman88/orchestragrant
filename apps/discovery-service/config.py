from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ENV: str = "development"
    DEBUG: bool = False
    DATABASE_URL_SYNC: str = ""
    GRANTS_GOV_API_KEY: str = ""
    CANDID_CLIENT_ID: str = ""
    CANDID_CLIENT_SECRET: str = ""
    SENTRY_DSN: str = ""
    # How many grants to fetch per source per run
    GRANTS_GOV_PAGE_SIZE: int = 25
    GRANTS_GOV_MAX_PAGES: int = 20
    CANDID_MAX_RESULTS: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
