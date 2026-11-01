from aiogram import Router

from . import cbs, chat_member, chat_migrate, cmds, get_user_message

router = Router()

router.include_routers(
    cbs.router,
    cmds.router,
    chat_member.router,
    chat_migrate.router,
    get_user_message.router
)
