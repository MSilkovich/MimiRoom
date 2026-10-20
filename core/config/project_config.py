"""Глобальные настройки приложения (проект + безопасность)."""

from dotenv import load_dotenv

from pydantic import Field
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    DB_ECHO: bool
    PROJECT_NAME: str
    VERSION: str
    DEBUG: bool
    CORS_ALLOWED_ORIGINS: str


settings_app = Settings()
