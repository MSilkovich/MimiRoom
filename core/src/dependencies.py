from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.db_helper import db_helper
from .middleware.auth import get_current_user
from .repositories.uow import SqlAlchemyUnitOfWork
from .repositories.base_uow import UnitOfWork
from src.models.user import User


async def get_session() -> AsyncIterator[AsyncSession]:
    """Отдаёт сессию БД для контроллеров (rollback/close на выходе)."""
    async with db_helper.get_db_session() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def get_uow_factory():
    """Фабрика Unit of Work на базе session_factory приложения.

    FastAPI кэширует результат зависимости в пределах запроса, а каждый
    ``async with uow`` внутри сервиса создаёт собственную транзакцию.
    """

    def uow_factory() -> UnitOfWork:
        return SqlAlchemyUnitOfWork(db_helper.session_factory)

    return uow_factory


UowFactoryDep = Annotated[UnitOfWork, Depends(get_uow_factory)]


def get_service(service_cls):
    """Зависимость FastAPI, строящая сервис поверх фабрики Unit of Work.

    Раньше в эндпоинты напрямую подавали ``get_uow_factory`` (фабрику), а
    затем вызывали на ней методы сервиса — из-за чего реальные CRUD-роуты
    падали с AttributeError. Здесь фабрика правильно оборачивается в сервис.
    """

    def _get_service(uow_factory=Depends(get_uow_factory)):
        return service_cls(uow_factory)

    return _get_service


# Обязательная аутентификация
CurrentUserDep = Annotated[User, Depends(get_current_user)]
