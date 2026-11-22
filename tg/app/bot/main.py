from __future__ import annotations

import asyncio
from typing import cast

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import PRODUCTION, TEST
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.webhook.aiohttp_server import (
    SimpleRequestHandler,
    ip_filter_middleware,
    setup_application,
)
from aiogram.webhook.security import DEFAULT_TELEGRAM_NETWORKS, IPFilter
from aiohttp import web
from aiohttp.typedefs import Middleware

import errors
import handlers
from config.project_config import settings_app
from config.telegram_config import settings_telegram
from middlewares.check_chat_middleware import CheckChatMiddleware
from middlewares.check_user_middleware import CheckUserMiddleware
from services import close_redis, run_response_consumer
from utils.logging import get_logger, setup_logging

logger = get_logger(__name__)

# Фоновые задачи процесса (consumer ответов engine).
_background_tasks: list[asyncio.Task] = []


async def _response_consumer_safe(bot: Bot) -> None:
    """Держим consumer живым: при падении перезапускаем через паузу."""
    while True:
        try:
            await run_response_consumer(bot)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Response consumer crashed, restarting in 5s")
            await asyncio.sleep(5)


async def startup(bot: Bot, **_kwargs) -> None:
    await bot.delete_webhook(drop_pending_updates=True)

    if not settings_telegram.DEV:
        await bot.set_webhook(
            url=settings_telegram.WEBHOOK_URL.get_secret_value(),
            secret_token=settings_telegram.WEBHOOK_SECRET_TOKEN.get_secret_value(),
        )

    # Слушаем ответы engine из Redis и доставляем в Telegram.
    task = asyncio.create_task(
        _response_consumer_safe(bot), name="tg-response-consumer"
    )
    _background_tasks.append(task)

    logger.info(
        "Bot started: %s v%s (dev=%s, webhooks=%s)",
        settings_app.PROJECT_NAME,
        settings_app.VERSION,
        settings_telegram.DEV,
        settings_telegram.WEBHOOKS,
    )


async def shutdown(**_kwargs) -> None:
    for task in _background_tasks:
        task.cancel()
    for task in _background_tasks:
        try:
            await task
        except asyncio.CancelledError:
            pass
    _background_tasks.clear()

    await close_redis()
    logger.info("Bot stopped")


def _build_bot() -> Bot:
    token = settings_telegram.BOT_TOKEN.get_secret_value()
    if not token or token == "CHANGE_ME":
        raise SystemExit(
            "BOT_TOKEN не задан. Укажите его в tg/.env (см. tg/.env.example)."
        )

    api = TEST if settings_telegram.TEST_SERVER is True else PRODUCTION
    return Bot(
        token=token,
        session=AiohttpSession(api=api),
        default=DefaultBotProperties(parse_mode="HTML"),
    )


async def main() -> None:
    setup_logging()
    logger.info("Starting %s v%s", settings_app.PROJECT_NAME, settings_app.VERSION)

    bot = _build_bot()

    dp = Dispatcher(
        events_isolation=SimpleEventIsolation(),
        developer_id=settings_telegram.DEVELOPER_ID,
    )
    dp.update.outer_middleware(CheckChatMiddleware())
    dp.update.outer_middleware(CheckUserMiddleware())
    dp.include_routers(handlers.router, errors.router)
    dp.startup.register(startup)
    dp.shutdown.register(shutdown)

    if settings_telegram.WEBHOOKS:
        app = web.Application(
            middlewares=[
                cast(Middleware, ip_filter_middleware(IPFilter(DEFAULT_TELEGRAM_NETWORKS))),
            ],
        )

        SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
            secret_token=settings_telegram.WEBHOOK_SECRET_TOKEN.get_secret_value(),
        ).register(app, "/webhook")
        setup_application(app, dp, bot=bot)

        await web._run_app(app, host="0.0.0.0", port=8080)  # noqa: S104, SLF001
    else:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
