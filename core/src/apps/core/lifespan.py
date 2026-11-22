from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.apps.core.logging import setup_logging, get_logger
from config.project_config import settings_app
from src.services.link_code_service import close_redis as close_link_code_redis
from src.services.health_service import start_health_monitor, stop_health_monitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Старт/остановка приложения.

    Сюда добавляем всё, что нужно поднять один раз на процесс:
    - publisher RabbitMQ / Kafka
    - redis-клиент
    - пул HTTP-клиентов
    - прогрев кэшей

    Всё кладём в ``app.state`` и достаём через ``Depends`` в deps.py.
    """
    # startup
    setup_logging()

    logger = get_logger(__name__)
    logger.info("Application '%s' v%s initialized",
                settings_app.PROJECT_NAME, settings_app.VERSION)

    logger.info(r"""
                __  __ _ __  __ _ ____                       
                |  \/  (_)  \/  (_)  _ \ ___   ___  _ __ ___  
                | |\/| | | |\/| | | |_) / _ \ / _ \| '_ ` _ \ 
                | |  | | | |  | | |  _ < (_) | (_) | | | | | |
                |_|  |_|_|_|  |_|_|_| \_\___/ \___/|_| |_| |_|
                """)

    await start_health_monitor()

    try:
        yield
    finally:
        # shutdown
        await stop_health_monitor()
        await close_link_code_redis()
