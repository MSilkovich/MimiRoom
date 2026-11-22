"""Consumer ответов engine из ``bot:responses`` -> отправка пользователю.

Ответ (``engine.src.schemas.outgoing.OutgoingMessage``) содержит:
``user_id, provider, channel, external_id, text, original_message_id, metadata``.
Нам нужны ``provider`` (фильтр), ``channel`` (куда отправить) и ``text``.

Группа consumer'а у бота своя (``REDIS_RESPONSE_GROUP_NAME``), поэтому бот
получает копию всех ответов и отбрасывает чужих провайдеров.
"""

from __future__ import annotations

from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config.core_config import settings_core
from config.redis_config import settings_redis
from utils.logging import get_logger

from .redis_client import ensure_response_group, get_redis

logger = get_logger(__name__)

_STREAM = settings_redis.REDIS_RESPONSE_STREAM_NAME
_GROUP = settings_redis.REDIS_RESPONSE_GROUP_NAME
_CONSUMER = settings_redis.REDIS_RESPONSE_CONSUMER_NAME


def _parse_response(fields: dict[str, str]) -> tuple[str, int] | None:
    """Вернуть (text, chat_id) если ответ адресован этому боту, иначе None."""
    if fields.get("provider") != settings_core.CORE_PROVIDER:
        return None

    text = fields.get("text")
    channel = fields.get("channel")
    if not text or not channel:
        logger.warning("Skip malformed response: %s", fields)
        return None

    # Для анонимных гостей engine получает channel вида "<chat_id>:<external_id>",
    # чтобы не смешивать историю в группах. Отправляем в настоящий chat_id.
    chat_part = channel.split(":", 1)[0]
    try:
        chat_id = int(chat_part)
    except (TypeError, ValueError):
        logger.warning("Skip response with bad channel=%r", channel)
        return None

    return text, chat_id


async def _deliver(bot: Bot, fields: dict[str, str]) -> None:
    parsed = _parse_response(fields)
    if parsed is None:
        return
    text, chat_id = parsed

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=None,
            disable_web_page_preview=True,
        )
        logger.info(
            "Response delivered: chat=%s original_message_id=%s text_len=%d",
            chat_id, fields.get("original_message_id"), len(text),
        )
    except TelegramAPIError:
        logger.exception(
            "Failed to deliver response to chat=%s (acked, will not retry)", chat_id
        )


async def _ack(r: Any, msg_id: str) -> None:
    await r.xack(_STREAM, _GROUP, msg_id)


async def _drain_pending(bot: Bot, r: Any) -> None:
    """Дочитать свои pending-ответы (id '0') после рестарта."""
    while True:
        results = await r.xreadgroup(
            groupname=_GROUP,
            consumername=_CONSUMER,
            streams={_STREAM: "0"},
            count=settings_redis.REDIS_READ_COUNT,
        )
        if not results:
            break
        empty = True
        for _stream, messages in results:
            if messages:
                empty = False
            for msg_id, fields in messages:
                await _deliver(bot, fields)
                await _ack(r, msg_id)
        if empty:
            break
    logger.info("Response pending drain finished")


async def run_response_consumer(bot: Bot) -> None:
    """Бесконечный цикл чтения ответов engine и отправки их в Telegram."""
    await ensure_response_group()
    r = await get_redis()

    await _drain_pending(bot, r)

    logger.info(
        "Response consumer started: stream=%s group=%s consumer=%s",
        _STREAM, _GROUP, _CONSUMER,
    )
    while True:
        results = await r.xreadgroup(
            groupname=_GROUP,
            consumername=_CONSUMER,
            streams={_STREAM: ">"},
            count=settings_redis.REDIS_READ_COUNT,
            block=settings_redis.REDIS_BLOCK_MS,
        )
        if not results:
            continue
        for _stream, messages in results:
            for msg_id, fields in messages:
                await _deliver(bot, fields)
                await _ack(r, msg_id)
