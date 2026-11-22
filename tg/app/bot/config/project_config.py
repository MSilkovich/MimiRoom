"""Глобальные настройки приложения."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "MimiRoom/tg-bot"
    VERSION: str = "0.0.1"


settings_app = Settings()
