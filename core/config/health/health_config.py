"""Настройки healthcheck-монитора."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Как часто фоновый монитор в реальности дергает БД/Redis.
    HEALTHCHECK_INTERVAL_SEC: int = Field(default=30)
    # Максимальное время одной проверки.
    HEALTHCHECK_TIMEOUT_SEC: float = Field(default=3.0)


settings_health = Settings()
