from fastapi import APIRouter
from config.project_config import settings_app


def get_apps_router() -> APIRouter:
    """Вернуть объединённый роутер."""

    from .routers import auth_router
    from .routers import measure_unit_router
    from .routers import pet_type_router
    from .routers import breed_router
    from .routers import storage_router
    from .routers import service_router, service_router_service
    from .routers import pet_router
    from .routers import book_router
    from .routers import user_router, user_router_service
    from .routers import staff_router

    router = APIRouter(prefix=f"/api/v{settings_app.VERSION}")

    router.include_router(auth_router)
    router.include_router(measure_unit_router)
    router.include_router(pet_type_router)
    router.include_router(breed_router)
    router.include_router(storage_router)
    router.include_router(service_router)
    router.include_router(service_router_service)
    router.include_router(pet_router)
    router.include_router(book_router)
    router.include_router(user_router)
    router.include_router(user_router_service)
    router.include_router(staff_router)

    return router
