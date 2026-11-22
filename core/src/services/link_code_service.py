"""Одноразовые коды привязки внешнего провайдера (Telegram) к пользователю core.

Код генерируется по запросу авторизованного пользователя (ЛК), хранится в
Redis с коротким TTL и удаляется атомарно при использовании. В БД код не
пишем: это временный секрет, а не сущность домена.

Ключ: ``{LINK_CODE_KEY_PREFIX}:{code}`` -> ``"{user_id}|{provider}"``.
"""

from __future__ import annotations

import secrets
import string
from typing import Optional

import redis.asyncio as redis

from config.redis import settings_redis
from src.apps.core.logging import get_logger
from src.models.enums.provider import Provider

logger = get_logger(__name__)

_ALPHABET = string.ascii_letters + string.digits

_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Singleton-клиент Redis, создаётся лениво."""
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
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
        logger.info("Redis client closed")


def _key(code: str) -> str:
    return f"{settings_redis.LINK_CODE_KEY_PREFIX}:{code}"


def _generate_code() -> str:
    return "".join(
        secrets.choice(_ALPHABET) for _ in range(settings_redis.LINK_CODE_LENGTH)
    )


async def issue_link_code(user_id: int, provider: Provider) -> str:
    """Сгенерировать одноразовый код для привязки ``provider`` к ``user_id``."""
    r = await get_redis()
    value = f"{user_id}|{provider.value}"

    for _ in range(5):
        code = _generate_code()
        created = await r.set(
            _key(code), value, ex=settings_redis.LINK_CODE_TTL_SEC, nx=True
        )
        if created:
            logger.info(
                "Link code issued: user_id=%s provider=%s ttl=%ss",
                user_id, provider.value, settings_redis.LINK_CODE_TTL_SEC,
            )
            return code

    raise RuntimeError("Failed to generate unique link code")


async def consume_link_code(code: str, provider: Provider) -> int | None:
    """Атомарно забрать код и вернуть user_id.

    Возвращает ``None``, если код отсутствует/истёк или выпущен для другого
    провайдера. Код в любом случае считается использованным.
    """
    r = await get_redis()
    value = await r.getdel(_key(code))
    if not value:
        logger.warning("Link code not found or expired")
        return None

    try:
        raw_user_id, raw_provider = value.split("|", 1)
        user_id = int(raw_user_id)
    except (ValueError, TypeError):
        logger.error("Malformed link code payload: %r", value)
        return None

    if raw_provider != provider.value:
        logger.warning(
            "Link code provider mismatch: expected=%s got=%s",
            provider.value, raw_provider,
        )
        return None

    logger.info("Link code consumed: user_id=%s provider=%s", user_id, provider.value)
    return user_id
