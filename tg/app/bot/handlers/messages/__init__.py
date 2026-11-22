from aiogram import Router

from . import chat

router = Router()
router.include_router(chat.router)
