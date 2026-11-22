"""Настройки клиента core-сервиса (backend API)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    CORE_BASE_URL: str = "http://core:30010"
    CORE_TIMEOUT_SEC: float = 15.0

    # Секрет сервисных JWT (совпадает с core.SERVICE_JWT_SECRET).
    CORE_SERVICE_SECRET: str = ""
    CORE_SERVICE_ALG: str = "HS256"

    # Провайдер, под которым бот представляется в core.
    CORE_PROVIDER: str = "telegram"

    # Путь ручки привязки/поиска связки.
    CORE_LINK_PATH: str = "/api/v0.0.1/users/link"


settings_core = Settings()
