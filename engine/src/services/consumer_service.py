"""Consumer-сервис: читает задачи из Redis Stream и передаёт в handler."""

import asyncio
import logging

import redis.asyncio as redis

from src.logging import get_logger
from config.redis import settings_redis
from .redis_connection import get_redis
from .llm_service import process_message

logger = get_logger(__name__)


async def _handle_one(msg_id: str, fields: dict) -> None:
    """Обработать одно сообщение. Не делает ACK — это ответственность вызывающего."""
    try:
        await process_message(fields)
    except Exception:
        logger.exception("Failed to process message %s", msg_id)
        raise


async def _drain_pending(r: redis.Redis) -> None:
    """Фаза 1: обработать свои pending-сообщения (ID '0')."""
    while True:
        results = await r.xreadgroup(
            groupname=settings_redis.REDIS_GROUP_NAME,
            consumername=settings_redis.REDIS_CONSUMER_NAME,
            streams={settings_redis.REDIS_STREAM_NAME: "0"},
            count=settings_redis.REDIS_READ_COUNT,
        )
        if not results:
            break
        for _stream, messages in results:
            if not messages:
                return
            for msg_id, fields in messages:
                try:
                    await _handle_one(msg_id, fields)
                    await r.xack(
                        settings_redis.REDIS_STREAM_NAME,
                        settings_redis.REDIS_GROUP_NAME,
                        msg_id,
                    )
                except Exception:
                    # не ACK'аем — сообщение останется pending
                    pass
    logger.info("Pending drain finished")


async def _janitor(r: redis.Redis) -> None:
    """Фаза 3: периодически забирать сообщения «мёртвых» consumer'ов."""
    while True:
        await asyncio.sleep(settings_redis.REDIS_JANITOR_INTERVAL_SEC)
        try:
            # XAUTOCLAIM возвращает (next_cursor, claimed_messages, deleted_ids)
            next_cursor = "0-0"
            while True:
                next_cursor, claimed, _deleted = await r.xautoclaim(
                    name=settings_redis.REDIS_STREAM_NAME,
                    groupname=settings_redis.REDIS_GROUP_NAME,
                    consumername=settings_redis.REDIS_CONSUMER_NAME,
                    min_idle_time=settings_redis.REDIS_CLAIM_MIN_IDLE_MS,
                    start_id=next_cursor,
                    count=settings_redis.REDIS_READ_COUNT,
                )
                if not claimed:
                    break
                for msg_id, fields in claimed:
                    try:
                        await _handle_one(msg_id, fields)
                        await r.xack(
                            settings_redis.REDIS_STREAM_NAME,
                            settings_redis.REDIS_GROUP_NAME,
                            msg_id,
                        )
                    except Exception:
                        pass  # останется pending для следующей попытки
                if next_cursor == "0-0":
                    break
        except Exception:
            logger.exception("Janitor cycle failed")


async def run_consumer() -> None:
    """Точка входа: запускает drain + main loop + janitor."""
    r = await get_redis()

    # Фаза 1: дочитать своё pending
    await _drain_pending(r)

    # Фаза 3: janitor в фоне
    janitor_task = asyncio.create_task(_janitor(r))

    # Фаза 2: main loop
    try:
        while True:
            results = await r.xreadgroup(
                groupname=settings_redis.REDIS_GROUP_NAME,
                consumername=settings_redis.REDIS_CONSUMER_NAME,
                streams={settings_redis.REDIS_STREAM_NAME: ">"},
                count=settings_redis.REDIS_READ_COUNT,
                block=settings_redis.REDIS_BLOCK_MS,
            )
            if not results:
                continue
            for _stream, messages in results:
                for msg_id, fields in messages:
                    try:
                        await _handle_one(msg_id, fields)
                        await r.xack(
                            settings_redis.REDIS_STREAM_NAME,
                            settings_redis.REDIS_GROUP_NAME,
                            msg_id,
                        )
                    except Exception:
                        # не ACK'аем — сообщение останется в PEL
                        pass
    finally:
        janitor_task.cancel()
        try:
            await janitor_task
        except asyncio.CancelledError:
            pass
