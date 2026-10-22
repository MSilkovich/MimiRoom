"""Глобальные настройки приложения."""

from dotenv import load_dotenv

from pydantic import Field
from pydantic_settings import BaseSettings


load_dotenv()


class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str


settings_app = Settings()
