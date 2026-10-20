from fastapi import APIRouter
from config.project_config import settings_app


def get_apps_router() -> APIRouter:
    """Вернуть объединённый роутер."""

    from .routers.auth import router as auth_router
    from .routers.measure_unit import router as measure_unit_router
    from .routers.pet_type import router as pet_type_router
    from .routers.breed import router as breed_router
    from .routers.storage import router as storage_router
    from .routers.service import router as service_router
    from .routers.pet import router as pet_router
    from .routers.book import router as book_router
    from .routers.users import router as users_router

    router = APIRouter(f"/api/v{settings_app.VERSION}")

    router.include_router(auth_router, prefix="/auth")
    router.include_router(measure_unit_router, prefix="/measure-units")
    router.include_router(pet_type_router, prefix="/pet-types")
    router.include_router(breed_router, prefix="/breeds")
    router.include_router(storage_router, prefix="/storages")
    router.include_router(service_router, prefix="/services")
    router.include_router(pet_router, prefix="/pets")
    router.include_router(book_router, prefix="/books")
    router.include_router(users_router, prefix="/users")

    return router
