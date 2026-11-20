"""Хранилище истории диалога в Redis.

Каждый диалог — Redis List с ключом ``dialog:{user_id}:{channel}``.
Элементы списка — JSON-строки вида ``{"role": "user", "content": "..."}``.

TTL (15 минут по умолчанию) обновляется при каждом append().
Если диалог не пополнялся дольше TTL — ключ удаляется Redis'ом автоматически.

В будущем: при каждом append() можно дублировать сообщение в PostgreSQL
для долговременного хранения. Этот класс этого не делает — его задача
только быстрая загрузка/запись в Redis.
"""

import json

from src.logging import get_logger
from config.redis import settings_redis
from src.services.redis_connection import get_redis

logger = get_logger(__name__)

_DIALOG_KEY_PREFIX = "dialog"


def _key(user_id: int, channel: str) -> str:
    """Сформировать ключ Redis для диалога пользователя."""
    return f"{_DIALOG_KEY_PREFIX}:{user_id}:{channel}"


class RedisMemoryStore:
    """MemoryStore на Redis List с TTL.

    Имплементирует контракт ``MemoryStore`` (Protocol из .base).
    """

    async def load(self, user_id: int, channel: str) -> list[dict]:
        """Загрузить всю историю диалога из Redis.

        Returns:
            Список сообщений ``[{"role": ..., "content": ...}, ...]``
            в хронологическом порядке (от старых к новым).
            Пустой список, если диалога нет или он истёк по TTL.
        """
        key = _key(user_id, channel)
        r = await get_redis()

        raw_messages: list[str] = await r.lrange(key, 0, -1)
        if not raw_messages:
            return []

        history: list[dict] = []
        for raw in raw_messages:
            try:
                msg = json.loads(raw)
                history.append(msg)
            except json.JSONDecodeError:
                logger.warning(
                    "Skipping invalid JSON in dialog key '%s': %s",
                    key, raw[:120],
                )
                continue

        logger.debug(
            "Loaded %d messages for dialog key '%s'",
            len(history), key,
        )
        return history

    async def append(self, user_id: int, channel: str, message: dict) -> None:
        """Добавить одно сообщение в историю и обновить TTL.

        Args:
            user_id: Внутренний ID пользователя.
            channel: Канал (чат/тред) в провайдере.
            message: Словарь вида ``{"role": "user", "content": "..."}``.
        """
        key = _key(user_id, channel)
        r = await get_redis()

        raw = json.dumps(message, ensure_ascii=False)
        await r.rpush(key, raw)
        await r.expire(key, settings_redis.DIALOG_TTL_SEC)

        logger.debug(
            "Appended message (role=%s) to dialog key '%s', "
            "TTL reset to %ds",
            message.get("role"), key, settings_redis.DIALOG_TTL_SEC,
        )

    async def clear(self, user_id: int, channel: str) -> None:
        """Очистить историю диалога (удалить ключ)."""
        key = _key(user_id, channel)
        r = await get_redis()
        await r.delete(key)
        logger.info("Dialog key '%s' cleared", key)
