"""Асинхронное подключение к Redis (singleton) и consumer group."""

from typing import Optional

import redis.asyncio as redis

from config.redis_config import settings_redis
from utils.logging import get_logger

logger = get_logger(__name__)

_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Вернуть singleton-клиент Redis. Создаётся лениво."""
    global _client
    if _client is None:
        _client = redis.from_url(
            settings_redis.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            # Должен быть больше REDIS_BLOCK_MS, иначе блокирующий XREADGROUP
            # падает с "Timeout reading" (дефолт redis-py 8.x — 5с).
            socket_timeout=settings_redis.REDIS_SOCKET_TIMEOUT_SEC,
            socket_connect_timeout=settings_redis.REDIS_SOCKET_TIMEOUT_SEC,
            health_check_interval=settings_redis.REDIS_HEALTH_CHECK_INTERVAL_SEC,
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


async def ensure_response_group() -> None:
    """Создать consumer group на response-стриме, если её ещё нет.

    Своя группа нужна, чтобы бот получал все ответы engine и сам фильтровал
    их по провайдеру, не конкурируя с другими адаптерами.
    """
    r = await get_redis()
    try:
        await r.xgroup_create(
            name=settings_redis.REDIS_RESPONSE_STREAM_NAME,
            groupname=settings_redis.REDIS_RESPONSE_GROUP_NAME,
            id="$",
            mkstream=True,
        )
        logger.info(
            "Response consumer group '%s' created for stream '%s'",
            settings_redis.REDIS_RESPONSE_GROUP_NAME,
            settings_redis.REDIS_RESPONSE_STREAM_NAME,
        )
    except redis.ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
        logger.debug("Response consumer group already exists")
