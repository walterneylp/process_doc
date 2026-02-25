from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Enterprise Processing Engine"
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-this-secret"
    app_enc_key: str = "change-me-32-byte-key"
    app_jwt_algorithm: str = "HS256"
    app_access_token_expire_minutes: int = 120

    database_url: str = "postgresql+psycopg2://epe:epe@localhost:5432/epe"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    storage_root: str = "./storage"
    smtp_from: str = "no-reply@epe.local"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
