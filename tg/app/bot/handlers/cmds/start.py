"""Команда /start, в т.ч. deep-link привязка Telegram к аккаунту в ЛК.

Сценарий привязки:
1. Пользователь в ЛК жмёт «Привязать Telegram».
2. ЛК выдаёт ссылку ``https://t.me/<bot>?start=<PAYLOAD>``.
3. Пользователь открывает бота -> /start <PAYLOAD>.
4. Бот разбирает payload, зовёт core ``POST /users/link`` и кэширует связку.

Формат PAYLOAD и требования к core см. ``utils/deep_link.py`` и README.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.core_client import CoreClient, CoreError
from services.link_cache import remember_link, resolve_user_id
from utils.callback_datas import UniversalWindowCloseCB
from utils.deep_link import LinkPayload, parse_start_payload
from utils.logging import get_logger

router = Router()
logger = get_logger(__name__)

_client = CoreClient()


def _close_keyboard(owner_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Закрыть",
                    callback_data=UniversalWindowCloseCB(
                        owner_id=owner_id).pack(),
                ),
            ],
        ],
    )


async def _send_welcome(msg: Message) -> None:
    """Приветствие с информацией о статусе привязки."""
    external_id = str(msg.from_user.id)
    user_id = await resolve_user_id(external_id)

    if user_id is None:
        text = (
            "👋 Здравствуйте!\n\n"
            "Чтобы я мог помочь с записью и вопросами, привяжите Telegram "
            "к аккаунту в личном кабинете.\n\n"
            "Откройте ЛК → «Привязать Telegram» и перейдите по ссылке оттуда."
        )
    else:
        text = (
            f"👋 Здравствуйте! Аккаунт привязан (#{user_id}).\n\n"
            "Напишите вопрос — я помогу с услугами, записью и подскажу детали."
        )

    await msg.answer(text, reply_markup=_close_keyboard(msg.from_user.id))


@router.message(CommandStart(deep_link=True))
async def start_cmd_with_deep_link(msg: Message, command: CommandObject) -> None:
    payload: LinkPayload = parse_start_payload(command.args)
    logger.info(
        "User %s started bot with deeplink: %s", msg.from_user.id, payload.raw
    )
    await _handle_link(msg, payload)


async def _handle_link(msg: Message, payload: LinkPayload) -> None:
    external_id = str(msg.from_user.id)

    if not payload.token:
        logger.warning("Deep-link without token: %s", payload.raw)
        await msg.answer(
            "⚠️ Не удалось прочитать ссылку привязки.\n"
            "Откройте личный кабинет и нажмите «Привязать Telegram» ещё раз."
        )
        return

    if payload.user_id is None:
        # Вариант «одноразовый код»: user_id должна определить core по коду.
        logger.warning(
            "Deep-link without user_id (opaque code): %s. "
            "Core должен уметь разрезолвить код.", payload.raw
        )
        await msg.answer(
            "⚠️ Ссылка устарела или неполная. "
            "Сформируйте новую ссылку в личном кабинете."
        )
        return

    try:
        await _client.create_link(
            user_id=payload.user_id,
            external_id=external_id,
            service_token=payload.token,
        )
    except CoreError as exc:
        logger.exception("Link failed for user_id=%s", payload.user_id)
        if exc.status == 409:
            await msg.answer(
                "ℹ️ Этот Telegram уже привязан к аккаунту. "
                "Если это ошибка — обратитесь в поддержку."
            )
        else:
            await msg.answer(
                "😔 Не удалось привязать аккаунт. Попробуйте позже "
                "или обратитесь в поддержку."
            )
        return

    await remember_link(payload.user_id, external_id)
    logger.info(
        "Telegram linked: external_id=%s -> user_id=%s", external_id, payload.user_id
    )
    await msg.answer(
        f"✅ Готово! Telegram привязан к аккаунту #{payload.user_id}.\n"
        "Теперь напишите вопрос — я на связи."
    )


@router.message(CommandStart(deep_link=False))
async def start_cmd(msg: Message) -> None:
    await _send_welcome(msg)
