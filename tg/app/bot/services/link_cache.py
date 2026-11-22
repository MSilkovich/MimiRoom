"""Кэш связки «внешний пользователь -> внутренний user_id».

Связка хранится в Redis и живёт ``LINK_CACHE_TTL_SEC`` (30 минут — TTL
диалога). Это избавляет от похода в core на каждое сообщение.

Логика:
- есть в кэше        -> отдаём user_id;
- есть негативный кэш -> None (непривязанный, чтобы не долбить core);
- нет в кэше         -> GET /users/link в core, затем кэшируем результат.
"""

from __future__ import annotations

from config.core_config import settings_core
from config.redis_config import settings_redis
from utils.logging import get_logger

from .core_client import CoreClient, CoreError
from .redis_client import get_redis

logger = get_logger(__name__)

_client = CoreClient()

_NULL = "null"


def _key(external_id: str) -> str:
    return (
        f"{settings_redis.LINK_CACHE_KEY_PREFIX}:"
        f"{settings_core.CORE_PROVIDER}:{external_id}"
    )


async def remember_link(user_id: int, external_id: str) -> None:
    """Положить/обновить связку в кэш с TTL."""
    r = await get_redis()
    await r.set(_key(external_id), str(user_id), ex=settings_redis.LINK_CACHE_TTL_SEC)
    logger.debug(
        "Link cached: external_id=%s -> user_id=%s (ttl=%ss)",
        external_id, user_id, settings_redis.LINK_CACHE_TTL_SEC,
    )


async def forget_link(external_id: str) -> None:
    """Удалить связку из кэша."""
    r = await get_redis()
    await r.delete(_key(external_id))


async def resolve_user_id(external_id: str) -> int | None:
    """Вернуть внутренний user_id по external_id или None, если не привязан."""
    r = await get_redis()
    key = _key(external_id)
    cached = await r.get(key)

    if cached is not None:
        if cached == _NULL:
            return None
        try:
            return int(cached)
        except (TypeError, ValueError):
            logger.warning("Invalid cached link value %r for key %s", cached, key)

    try:
        link = await _client.get_link(external_id)
    except CoreError as exc:
        # core недоступен / ручка не реализована — не кэшируем ошибку
        logger.warning(
            "Failed to resolve link for external_id=%s: %s", external_id, exc
        )
        return None

    if link and link.get("user_id") is not None:
        user_id = int(link["user_id"])
        await remember_link(user_id, external_id)
        return user_id

    # Не привязан — короткий негативный кэш.
    await r.set(key, _NULL, ex=settings_redis.LINK_NEGATIVE_CACHE_TTL_SEC)
    return None
