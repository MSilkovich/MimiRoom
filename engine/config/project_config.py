"""Глобальные настройки приложения."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str


settings_app = Settings()
