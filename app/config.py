from typing import Literal

from pydantic_settings import BaseSettings
from pydantic import validator, field_validator
import os


class Settings(BaseSettings):
    environment: Literal["development", "production"] = "development"
    domain: str = "cd64186.tw1.ru"
    cors_origins: list = ["http://localhost:8000", "http://127.0.0.1:8000"]
    secret_key: str
    database_url: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    @field_validator("CORS_ORIGINS", check_fields=False)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("database_url")
    def validate_database_url(cls, v):
        if v.startswith("postgresql"):
            # Заменяем синтаксис для совместимости
            v = v.replace("postgresql://", "postgresql+asyncpg://")
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False  # разрешаем регистронезависимое чтение из .env
        extra = "ignore"  # игнорируем лишние поля в .env, если они не нужны


settings = Settings()
