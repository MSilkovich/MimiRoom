"""Обработка обычных текстовых сообщений пользователя.

Поток: сообщение -> резолв привязки (с кэшем) -> задача в bot:tasks ->
ответ придёт из bot:responses (см. services/response_consumer.py).
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.types import Message

from services.link_cache import resolve_user_id
from services.task_publisher import publish_incoming
from utils.logging import get_logger

router = Router()
logger = get_logger(__name__)

_ALLOWED_CHAT_TYPES = {
    ChatType.PRIVATE,
    ChatType.GROUP,
    ChatType.SUPERGROUP,
}


@router.message(F.text, ~F.text.startswith("/"))
async def on_text_message(msg: Message) -> None:
    if msg.from_user is None or msg.from_user.is_bot:
        return
    if msg.chat.type not in _ALLOWED_CHAT_TYPES:
        return

    text = (msg.text or "").strip()
    if not text:
        return

    external_id = str(msg.from_user.id)
    user_id = await resolve_user_id(external_id)

    # Анонимный гость (не привязан к ЛК): работаем с user_id=0.
    # Канал делаем уникальным (chat_id:external_id), чтобы в группах
    # история разных гостей не смешивалась в engine (dialog:{user_id}:{channel}).
    channel = str(msg.chat.id)
    if user_id is None:
        user_id = 0
        channel = f"{msg.chat.id}:{external_id}"

    try:
        await publish_incoming(
            user_id=user_id,
            external_id=external_id,
            channel=channel,
            text=text,
            message_id=str(msg.message_id),
        )
    except Exception:  # noqa: BLE001 — не роняем хендлер из-за Redis
        logger.exception("Failed to publish incoming message")
        await msg.answer("😔 Сервис временно недоступен. Попробуйте позже.")
        return

    # Показываем «печатает», пока engine думает.
    try:
        await msg.bot.send_chat_action(chat_id=msg.chat.id, action="typing")
    except Exception:  # noqa: BLE001
        logger.debug("Failed to send chat action", exc_info=True)
