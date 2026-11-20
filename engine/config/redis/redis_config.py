from pydantic import Field
from uuid import uuid4

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)

    # Входной стрим / consumer group — сюда адаптеры кладут сообщения пользователей
    REDIS_STREAM_NAME: str = Field(default="bot:tasks")
    REDIS_GROUP_NAME: str = Field(default="bot-engine")
    REDIS_CONSUMER_NAME: str = Field(default=f"worker-{uuid4().hex[:8]}")

    # Выходной стрим — сюда engine кладёт ответ LLM, откуда адаптер его забирает
    REDIS_RESPONSE_STREAM_NAME: str = Field(default="bot:responses")
    REDIS_RESPONSE_MAXLEN: int = Field(default=1000)

    # Поведение consumer'а - можно оставить дефолтными
    REDIS_READ_COUNT: int = Field(default=10)
    REDIS_BLOCK_MS: int = Field(default=5000)
    REDIS_CLAIM_MIN_IDLE_MS: int = Field(default=60_000)
    REDIS_JANITOR_INTERVAL_SEC: int = Field(default=30)

    # Память диалогов (Redis List)
    DIALOG_TTL_SEC: int = Field(
        default=900,
        description="Время жизни ключа диалога в секундах. "
        "15 минут = 900 с. Если диалог не пополнялся дольше — ключ удаляется.",
    )

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings_redis = Settings()
