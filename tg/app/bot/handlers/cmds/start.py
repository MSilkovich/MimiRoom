"""Команда /start, в т.ч. deep-link привязка Telegram к аккаунту в ЛК.

Единственный способ привязки — одноразовый код:
1. Пользователь в ЛК жмёт «Привязать Telegram».
2. ЛК выдаёт ссылку ``https://t.me/<bot>?start=<code>`` (код выпускает core).
3. Пользователь открывает бота -> /start <code>.
4. Бот обменивает код на связку: core ``POST /users/link/code/consume``.
5. Бот кэширует связку ``external_id -> user_id``.

Разбор payload см. ``utils/deep_link.py`` и README.
"""

from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from services.core_client import CoreClient, CoreError
from services.link_cache import remember_link, resolve_user_id
from utils.escape_helper import escape_md_v2
from utils.callback_datas import UniversalWindowCloseCB
from utils.deep_link import parse_start_code
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
            "Можно пользоваться и без привязки — я помогу выбрать услугу "
            "и записаться.\n\n"
            "Если привяжете Telegram в личном кабинете (ЛК → «Привязать Telegram»), "
            "я буду помнить ваши данные и питомцев."
        )
    else:
        text = (
            f"👋 Здравствуйте! Аккаунт привязан (#{user_id}).\n\n"
            "Напишите вопрос — я помогу с услугами, записью и подскажу детали."
        )

    await msg.answer(escape_md_v2(text), reply_markup=_close_keyboard(msg.from_user.id))


@router.message(CommandStart(deep_link=True))
async def start_cmd_with_deep_link(msg: Message, command: CommandObject) -> None:
    code = parse_start_code(command.args)
    logger.info(
        "User %s started bot with deeplink: %r", msg.from_user.id, command.args
    )
    await _handle_link(msg, code)


async def _handle_link(msg: Message, code: str | None) -> None:
    external_id = str(msg.from_user.id)

    if not code:
        logger.warning("Deep-link without valid code: %r", code)
        await msg.answer(escape_md_v2(
            "⚠️ Не удалось прочитать ссылку привязки.\n"
            "Откройте личный кабинет и нажмите «Привязать Telegram» ещё раз."
        ))
        return

    try:
        # Единственный формат привязки: одноразовый короткий код из ЛК.
        link = await _client.consume_link_code(
            code=code,
            external_id=external_id,
        )
        if not link or link.get("user_id") is None:
            raise CoreError("Empty response from link code consume")
        linked_user_id = int(link["user_id"])
    except CoreError as exc:
        logger.warning("Link failed for external_id=%s: %s", external_id, exc)
        if exc.status == 409:
            await msg.answer(escape_md_v2(
                "ℹ️ Этот Telegram уже привязан к другому аккаунту. "
                "Если это ошибка — обратитесь в поддержку."
            ))
        elif exc.status in (400, 404, 422):
            await msg.answer(escape_md_v2(
                "⚠️ Ссылка привязки недействительна или истекла.\n"
                "Сформируйте новую ссылку в личном кабинете."
            ))
        else:
            await msg.answer(escape_md_v2(
                "😔 Не удалось привязать аккаунт. Попробуйте позже "
                "или обратитесь в поддержку."
            ))
        return

    await remember_link(linked_user_id, external_id)
    logger.info(
        "Telegram linked: external_id=%s -> user_id=%s", external_id, linked_user_id
    )
    await msg.answer(escape_md_v2(
        f"✅ Готово! Telegram привязан к аккаунту #{linked_user_id}.\n"
        "Теперь напишите вопрос — я на связи."
    ))


@router.message(CommandStart(deep_link=False))
async def start_cmd(msg: Message) -> None:
    await _send_welcome(msg)
