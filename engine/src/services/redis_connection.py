"""Асинхронное подключение к Redis."""

from src.logging import get_logger
from typing import Optional

import redis.asyncio as redis

from config.redis import settings_redis

logger = get_logger(__name__)

_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Вернуть singleton-клиент Redis. Создаётся лениво при первом вызове."""
    global _client
    if _client is None:
        _client = redis.from_url(
            settings_redis.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        logger.info("Redis client created for %s", settings_redis.redis_url)
    return _client


async def close_redis() -> None:
    """Закрыть клиент и освободить пул соединений."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Redis client closed")


async def ensure_consumer_group() -> None:
    """Создать consumer group, если её ещё нет."""
    r = await get_redis()
    try:
        await r.xgroup_create(
            name=settings_redis.REDIS_STREAM_NAME,
            groupname=settings_redis.REDIS_GROUP_NAME,
            id="0",
            mkstream=True,
        )
        logger.info(
            "Consumer group '%s' created for stream '%s'",
            settings_redis.REDIS_GROUP_NAME,
            settings_redis.REDIS_STREAM_NAME,
        )
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise
        logger.debug("Consumer group already exists")
