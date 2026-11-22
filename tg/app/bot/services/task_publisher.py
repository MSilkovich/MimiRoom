"""Публикация входящего сообщения в task-стрим engine.

Формат полей = ``engine.src.schemas.incoming.IncomingMessage``:
``user_id, provider, channel, external_id, text, message_id, received_at``.
Все значения Redis Stream обязаны быть строками, поэтому приводим явно.

ВАЖНО: историю диалога (``dialog:{user_id}:{channel}``) ведёт сам engine
(``RedisMemoryStore``). Бот историю не дублирует — он только кладёт задачу.
"""

from __future__ import annotations

from datetime import datetime, timezone

from config.core_config import settings_core
from config.redis_config import settings_redis
from utils.logging import get_logger

from .redis_client import get_redis

logger = get_logger(__name__)


async def publish_incoming(
    *,
    user_id: int,
    external_id: str,
    channel: str,
    text: str,
    message_id: str,
    received_at: datetime | None = None,
) -> str:
    """Опубликовать задачу в ``REDIS_TASK_STREAM_NAME`` и вернуть id записи."""
    r = await get_redis()

    fields: dict[str, str] = {
        "user_id": str(user_id),
        "provider": settings_core.CORE_PROVIDER,
        "channel": str(channel),
        "external_id": str(external_id),
        "text": text,
        "message_id": str(message_id),
        "received_at": (received_at or datetime.now(timezone.utc)).isoformat(),
    }

    msg_id = await r.xadd(
        name=settings_redis.REDIS_TASK_STREAM_NAME,
        fields=fields,
    )
    logger.info(
        "Task published: stream=%s id=%s user_id=%s external_id=%s chat=%s",
        settings_redis.REDIS_TASK_STREAM_NAME, msg_id, user_id, external_id, channel,
    )
    return msg_id
