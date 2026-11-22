"""Настройки Telegram-бота (для формирования deep-link)."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Публичный username бота без @. Если пусто — deep_link не собирается.
    TG_BOT_USERNAME: str = ""


settings_tg = Settings()
