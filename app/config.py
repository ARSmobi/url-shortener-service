from pydantic_settings import BaseSettings
from pydantic import validator
import os


class Settings(BaseSettings):
    secret_key: str
    database_url: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    @validator("database_url")
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
