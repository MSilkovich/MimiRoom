"""Настройки healthcheck-монитора."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Как часто фоновый монитор в реальности дергает зависимости.
    HEALTHCHECK_INTERVAL_SEC: int = Field(default=30)
    # Максимальное время одной проверки.
    HEALTHCHECK_TIMEOUT_SEC: float = Field(default=3.0)

    # Проверять доступность core (backend API).
    HEALTHCHECK_BACKEND_ENABLED: bool = Field(default=True)
    # Проверять LLM (может быть дорого/rate-limit — по умолчанию выключено).
    HEALTHCHECK_LLM_ENABLED: bool = Field(default=False)


settings_health = Settings()
