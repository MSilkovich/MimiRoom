import os
import sys

from fastapi import FastAPI

from config.project_config import settings_app
from src.apps.core.routes import get_apps_router
from src.exceptions import register_exception_handlers
from src.middleware.auth import AuthMiddleware
from src.middleware.error import ErrorMiddleware
from .lifespan import lifespan

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_application() -> FastAPI:
    application = FastAPI(
        title=settings_app.PROJECT_NAME,
        debug=settings_app.DEBUG,
        version=settings_app.VERSION,
        lifespan=lifespan,
    )

    application.include_router(get_apps_router())

    # Порядок важен: последний добавленный — самый внешний
    application.add_middleware(AuthMiddleware)
    application.add_middleware(ErrorMiddleware)

    register_exception_handlers(application)

    return application


app = get_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("apps.core.main:app", host="0.0.0.0", port=8000, reload=True)
