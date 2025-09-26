from pydantic_settings import BaseSettings
from typing import List
from pydantic import field_validator

class Settings(BaseSettings):
    ENVIRONMENT: str
    SECRET_KEY: str
    DATABASE_URL: str
    DOMAIN: str
    CORS_ORIGINS: str  # Сначала считаем как строку
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()