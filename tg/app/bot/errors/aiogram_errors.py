"""Обработчик ошибок aiogram.

Раньше здесь создавался FileHandler("errors.log") на import-е, из-за чего в
контейнере (read-only /app, запуск от непривилегированного пользователя) бот
падал на старте. Теперь пишем через общий логгер приложения.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router

from utils.logging import get_logger

if TYPE_CHECKING:
    from aiogram.types import ErrorEvent

router = Router()
logger = get_logger(__name__)


@router.errors()
async def errors_handler(event: ErrorEvent) -> None:
    logger.exception(
        "Update handling failed: update=%s",
        event.update,
        exc_info=event.exception,
    )
