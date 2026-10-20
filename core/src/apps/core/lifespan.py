from contextlib import asynccontextmanager
from fastapi import FastAPI


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
    # --- startup ---
    # app.state.publisher = RabbitPublisher(...)
    # await app.state.publisher.connect()

    yield

    # --- shutdown ---
    # await app.state.publisher.close()
