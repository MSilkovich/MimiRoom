from aiogram import Router

from . import cbs, chat_member, chat_migrate, cmds, messages

router = Router()

router.include_routers(
    cbs.router,
    cmds.router,
    messages.router,
    chat_member.router,
    chat_migrate.router,
)
