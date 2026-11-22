"""Конфигурация TG-бота.

Единая точка загрузки `.env` (как в engine/core). Все настройки разложены по
доменным модулям и экспортируются как ``settings_*``.
"""

from dotenv import load_dotenv

# .env загружаем один раз до чтения настроек (pydantic-settings читает env).
load_dotenv()
