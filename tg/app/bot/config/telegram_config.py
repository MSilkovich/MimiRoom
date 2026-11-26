"""Настройки Telegram-бота (aiogram)."""

from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Режим разработки: True -> long polling, вебхук не выставляется.
    DEV: bool = True
    # Использовать тестовый сервер Telegram (только для отладки).
    TEST_SERVER: bool = False
    # Telegram user id разработчика (админ бота).
    DEVELOPER_ID: int = 0

    # Webhook-режим. Если False — long polling.
    WEBHOOKS: bool = False
    WEBHOOK_URL: SecretStr = SecretStr("")
    WEBHOOK_SECRET_TOKEN: SecretStr = SecretStr("")

    BOT_TOKEN: SecretStr = SecretStr("")

    PROXY_LINK: str | None = None


settings_telegram = Settings()
