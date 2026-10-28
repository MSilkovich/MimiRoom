from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.db_helper import db_helper
from src.context import get_current_user
from src.excpetions.auth import PermissionDeniedError
from src.permissions.bitmask import get_scope, has
from src.permissions.enums.permissions import Permission
from src.permissions.enums.scope import Scope
from src.permissions.permission_rule import PermissionRule
from .repositories.uow import SqlAlchemyUnitOfWork
from .repositories.base_uow import UnitOfWork
from src.models.user import User


async def get_session() -> AsyncIterator[AsyncSession]:
    """Отдаёт сессию БД для контроллеров (rollback/close на выходе)."""
    async with db_helper.get_db_session() as session:
        yield session


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


def require_perm(perm: Permission, min_scope: Scope = Scope.OWN):
    """Проверяет право и возвращает правило доступа."""
    async def _checker(user: User = Depends(get_current_user)) -> PermissionRule:
        scope = get_scope(user.permission_mask, perm)
        if not scope.allows(min_scope):
            raise PermissionDeniedError()  # TODO: подумать
        owner_id = user.user_id if scope == Scope.OWN else None
        return PermissionRule(permission=perm, scope=scope, owner_id=owner_id)
    return _checker


def require_role(*roles: str):
    async def _checker(user: User = Depends(get_current_user)) -> None:
        if user.role not in roles:
            raise PermissionDeniedError("У роли недостаточно прав")
        return None
    return _checker
