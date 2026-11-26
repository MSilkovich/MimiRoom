from fastapi import APIRouter
from config.project_config import settings_app


def get_apps_router() -> APIRouter:
    """Вернуть объединённый роутер."""

    from .routers.chat import router as chat_router
    from .routers.staff import router as staff_router

    router = APIRouter(prefix=f"/api/v{settings_app.VERSION}")

    router.include_router(chat_router)

    return router


def get_staff_router() -> APIRouter:
    """Роутер staff без версионного префикса."""
    from .routers import staff_router
    return staff_router
