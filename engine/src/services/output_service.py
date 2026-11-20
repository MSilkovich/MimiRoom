"""Сервис публикации ответов LLM в Redis Stream для адаптера."""

import json

from src.logging import get_logger
from config.redis import settings_redis
from .redis_connection import get_redis
from src.schemas.outgoing import OutgoingMessage

logger = get_logger(__name__)


async def publish_response(message: OutgoingMessage) -> None:
    """Опубликовать ответ LLM в response-стрим.

    Адаптер читает этот стрим и доставляет ответ пользователю.
    Все значения сериализуются в JSON-строки для совместимости с Redis Stream.
    """
    r = await get_redis()

    raw_body = message.model_dump(mode="json")
    # Redis XADD требует, чтобы все значения полей были строками.
    # Сериализуем каждое значение через json.dumps.
    fields: dict[str, str] = {
        k: json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
        for k, v in raw_body.items()
    }

    await r.xadd(
        name=settings_redis.REDIS_RESPONSE_STREAM_NAME,
        fields=fields,
        maxlen=settings_redis.REDIS_RESPONSE_MAXLEN,
        approximate=True,
    )
    logger.info(
        "Response published: user_id=%s provider=%s original_message_id=%s "
        "text_len=%d",
        message.user_id,
        message.provider,
        message.original_message_id,
        len(message.text),
    )
