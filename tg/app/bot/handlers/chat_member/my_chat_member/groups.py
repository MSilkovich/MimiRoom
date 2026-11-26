from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from aiogram import Bot, F, Router
from aiogram.enums import ChatType
from aiogram.filters import (
    ADMINISTRATOR,
    IS_NOT_MEMBER,
    LEAVE_TRANSITION,
    MEMBER,
    PROMOTED_TRANSITION,
    RESTRICTED,
    ChatMemberUpdatedFilter,
)
from aiogram.types import ChatMemberRestricted

from utils.escape_helper import escape_md_v2

if TYPE_CHECKING:
    from aiogram.types import ChatMemberAdministrator, ChatMemberMember, ChatMemberUpdated

router = Router()
logger = logging.getLogger(__name__)


@router.my_chat_member(
    ChatMemberUpdatedFilter(PROMOTED_TRANSITION),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def my_chat_member_promoted_transition(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    logger.info("Bot was promoted in chat %s", chat_member.chat.id)

    if TYPE_CHECKING:
        assert isinstance(chat_member.new_chat_member, ChatMemberAdministrator)

    can_delete_messages = chat_member.new_chat_member.can_delete_messages
    can_restrict_members = chat_member.new_chat_member.can_restrict_members
    can_invite_users = chat_member.new_chat_member.can_invite_users

    await bot.send_message(
        chat_id=chat_member.chat.id,
        text=escape_md_v2("❤️ Thank you for promoting me to an administrator!\n" +
                          "\n" +
                          "💬 For full functionality, I need the following rights:\n" +
                          f"{"'✅" if can_delete_messages else '❌'} Delete messages\n" +
                          f"{"'✅" if can_restrict_members else '❌'} Restrict members\n" +
                          f"{"'✅" if can_invite_users else '❌'} Invite users\n")
    )


@router.my_chat_member(
    ChatMemberUpdatedFilter(ADMINISTRATOR >> ADMINISTRATOR),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def my_chat_member_administrator_transition(chat_member: ChatMemberUpdated) -> None:
    logger.info("Bot admin rights was changed in chat %s", chat_member.chat.id)


@router.my_chat_member(
    ChatMemberUpdatedFilter(IS_NOT_MEMBER >> (MEMBER | +RESTRICTED)),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def my_chat_member_join_transition(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    logger.info("Bot was added to chat %s", chat_member.chat.id)

    if TYPE_CHECKING:
        assert isinstance(chat_member.new_chat_member,
                          ChatMemberMember | ChatMemberRestricted)

    if (
        isinstance(chat_member.new_chat_member, ChatMemberRestricted)
        and chat_member.new_chat_member.can_send_messages
    ):
        await bot.send_message(
            chat_id=chat_member.chat.id,
            text=escape_md_v2("❤️ Thank you for adding me to the chat.\n"
                              "\n"
                              "💬 For full functionality, I need the following rights:\n"
                              "❌ Delete messages\n"
                              "❌ Restrict members\n"
                              "❌ Invite users")
        )


@router.my_chat_member(
    ChatMemberUpdatedFilter(+RESTRICTED >> (MEMBER | +RESTRICTED)),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def my_chat_member_unrestricted_transition(chat_member: ChatMemberUpdated) -> None:
    logger.info("Bot was un/restricted in chat %s", chat_member.chat.id)


@router.my_chat_member(
    ChatMemberUpdatedFilter(ADMINISTRATOR >> (MEMBER | +RESTRICTED)),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def my_chat_member_demoted_transition(chat_member: ChatMemberUpdated, bot: Bot) -> None:
    logger.info("Bot was demoted in chat %s", chat_member.chat.id)

    await bot.send_message(
        chat_id=chat_member.chat.id,
        text=escape_md_v2(
            "My administrator rights have been revoked.\n\nI will continue to work in the chat, but with limited capabilities.")
    )


@router.my_chat_member(
    ChatMemberUpdatedFilter(LEAVE_TRANSITION),
    F.chat.type.in_({ChatType.GROUP, ChatType.SUPERGROUP}),
)
async def my_chat_member_leave_transition(chat_member: ChatMemberUpdated) -> None:
    logger.info("Bot was kicked from chat %s", chat_member.chat.id)
