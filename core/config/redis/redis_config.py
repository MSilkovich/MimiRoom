"""Настройки Redis для core (одноразовые коды привязки)."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)

    # Одноразовый код привязки: живёт недолго и удаляется после использования.
    LINK_CODE_KEY_PREFIX: str = Field(default="tg:link_code")
    LINK_CODE_TTL_SEC: int = Field(default=300)
    LINK_CODE_LENGTH: int = Field(default=12)

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings_redis = Settings()
