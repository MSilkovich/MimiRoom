import logging

from fastapi import FastAPI

from config.project_config import settings_app
from src.apps.engine.routes import get_apps_router
from .lifespan import lifespan


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings_app.PROJECT_NAME,
        debug=False,
        version=settings_app.VERSION,
        lifespan=lifespan,
        description="""
## О приложении

Сервис обработки сообщений пользователей через разные каналы
Адаптеры (например, TG бот, бот в Max или ВК) пересылают сообщение пользователя сюда,
ИИ обрабатывает ответ, при необходимости вызывает tools и возвращает ответ
""",
        contact={
            "name": "Команда поддержки",
            "email": "gnom.48.spb@gmail.com",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=[
            {
                "name": "staff",
                "description": "Служебные ручки",
            },
        ],
    )

    application.include_router(get_apps_router())

    return application


app = get_application()
