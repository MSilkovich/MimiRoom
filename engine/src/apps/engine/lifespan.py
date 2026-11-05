import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.logging import setup_logging, get_logger
from config.project_config import settings_app
from src.services import ensure_consumer_group, run_consumer, close_redis


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
    _    ___      _____             _            
   / \  |_ _|    | ____|_ __   __ _(_)_ __   ___ 
  / _ \  | |_____|  _| | '_ \ / _` | | '_ \ / _ \
 / ___ \ | |_____| |___| | | | (_| | | | | |  __/
/_/   \_\___|    |_____|_| |_|\__, |_|_| |_|\___|
                              |___/                         
                """)

    try:
        await ensure_consumer_group()
        consumer_task = asyncio.create_task(run_consumer())

        yield
    finally:
        # shutdown
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
        await close_redis()
