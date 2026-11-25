from collections.abc import AsyncIterator
from typing import Annotated, Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.database.db_helper import db_helper
from src.excpetions.auth import PermissionDeniedError
from src.middleware.auth import get_current_user as get_authenticated_user
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal
from src.permissions.bitmask import get_scope
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


def require_perm(
    perm: Permission,
    min_scope: Scope = Scope.OWN,
    owner_field: str | Callable[[User], str] = "who_create",
    allow_service: bool = False,
):
    """Проверяет уровень доступа и возвращает правило доступа.

    Args:
        perm: необходимое правило.
        min_scope: минимальный уровень правила.
        owner_field: колонка, по которой ограничивается OWN-доступ. Может быть
            callable(user) — например, для броней: клиент ограничивается
            ``client_id``, грумер — ``master_id``.
        allow_service: разрешать ли сервисные токены. Для shared-ручек
            (слоты, брони), которые дергает engine, включаем явно.

    Returns:
        PermissionRule: объект правила доступа.

    Raises:
        PermissionDeniedError: Если уровень права доступа недостаточен.
    """
    async def _checker(
        principal: Principal = Depends(get_principal),
    ) -> PermissionRule:
        if principal.is_service:
            if not allow_service:
                raise PermissionDeniedError("Сервисный токен сюда не допускается")
            return PermissionRule(
                permission=perm,
                scope=Scope.ALL,
                owner_id=None,
                owner_field=(
                    owner_field
                    if isinstance(owner_field, str)
                    else "who_create"
                ),
            )

        user = principal.user
        if user is None:
            raise PermissionDeniedError()

        scope = get_scope(user.permission_mask, perm)
        if not scope.allows(min_scope):
            raise PermissionDeniedError()

        field = owner_field(user) if callable(owner_field) else owner_field
        owner_id = user.user_id if scope == Scope.OWN else None
        return PermissionRule(
            permission=perm,
            scope=scope,
            owner_id=owner_id,
            owner_field=field,
        )
    return _checker


def require_role(*roles: str):
    async def _checker(user: User = Depends(get_authenticated_user)) -> None:
        if user.role not in roles:
            raise PermissionDeniedError("У роли недостаточно прав")
        return None
    return _checker


async def require_service(
    principal: Principal = Depends(get_principal),
) -> Principal:
    """Разрешить только сервисный токен (внутренние ручки /s/*)."""
    if not principal.is_service:
        raise PermissionDeniedError("Доступно только сервисному токену")
    return principal
