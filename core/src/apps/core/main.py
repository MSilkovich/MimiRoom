import logging

from fastapi import FastAPI

from config.project_config import settings_app
from src.apps.core.routes import get_apps_router
from src.middleware.auth import AuthMiddleware
from src.middleware.error import ErrorMiddleware
from .lifespan import lifespan


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings_app.PROJECT_NAME,
        debug=False,
        version=settings_app.VERSION,
        lifespan=lifespan,
    )

    application.include_router(get_apps_router())

    # Порядок важен: последний добавленный — самый внешний
    application.add_middleware(AuthMiddleware)
    application.add_middleware(ErrorMiddleware)

    return application


app = get_application()
