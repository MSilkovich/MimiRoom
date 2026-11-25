"""Настройки Redis и Redis Streams.

Имена стримов и группы должны совпадать с engine:
- task-стрим   — engine.REDIS_STREAM_NAME          (bot:tasks)
- response-стрим — engine.REDIS_RESPONSE_STREAM_NAME (bot:responses)
"""

from uuid import uuid4

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    REDIS_HOST: str = Field(default="localhost")
    REDIS_PORT: int = Field(default=6379)
    REDIS_DB: int = Field(default=0)
    REDIS_PASSWORD: str | None = Field(default=None)

    # Входной стрим engine — сюда бот публикует задачи.
    REDIS_TASK_STREAM_NAME: str = Field(default="bot:tasks")
    # Выходной стрим engine — здесь бот ждёт ответы LLM.
    REDIS_RESPONSE_STREAM_NAME: str = Field(default="bot:responses")

    # Своя consumer group на response-стриме (у каждого адаптера своя).
    REDIS_RESPONSE_GROUP_NAME: str = Field(default="tg-bot")
    REDIS_RESPONSE_CONSUMER_NAME: str = Field(
        default=f"tg-bot-{uuid4().hex[:8]}"
    )

    REDIS_READ_COUNT: int = Field(default=10)
    REDIS_BLOCK_MS: int = Field(default=5000)

    # ВАЖНО: в redis-py 8.x дефолтный socket_timeout = 5с. Блокирующий
    # XREADGROUP с block=5000мс при таком таймауте падает с
    # "TimeoutError: Timeout reading". Таймаут сокета обязан быть БОЛЬШЕ block.
    REDIS_SOCKET_TIMEOUT_SEC: float = Field(default=15)
    REDIS_HEALTH_CHECK_INTERVAL_SEC: int = Field(default=30)

    # Кэш связки «провайдер/external_id -> внутренний user_id».
    # TTL диалога = 30 минут.
    LINK_CACHE_KEY_PREFIX: str = Field(default="tg:link")
    LINK_CACHE_TTL_SEC: int = Field(default=1800)
    LINK_NEGATIVE_CACHE_TTL_SEC: int = Field(default=30)

    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


settings_redis = Settings()
