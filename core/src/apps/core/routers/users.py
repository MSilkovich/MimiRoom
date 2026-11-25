"""CRUD для пользователей (User).

Путь: /users*
- GET    /users                          — список пользователей
- GET    /users/{id}                     — один пользователь
- POST   /users                          — создать пользователя
- PUT    /users/{id}                     — обновить пользователя
- DELETE /users/{id}                     — удалить пользователя
TODO: дополнить для link
"""

from fastapi import APIRouter, Depends, Security

from src import dependencies as deps
from src.excpetions.auth import PermissionDeniedError
from src.excpetions.crud import NotFoundError
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal
from src.models.user import User
from src.permissions.bitmask import has
from src.permissions.enums.permissions import Permission
from src.permissions.enums.roles import Role
from src.permissions.enums.scope import Scope
from src.permissions.permission_rule import PermissionRule
from src.schemas.user import (
    UserCreate,
    UserProfileRead,
    UserRead,
    UserRoleUpdate,
    UserUpdate,
)
from src.schemas import Summary, UserSummary
from src.services.user_service import UserService
from src.middleware.auth import get_current_user, auth_bearer_scheme

router = APIRouter(prefix="/users", tags=["users"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[UserRead], dependencies=[
    Depends(deps.require_perm(Permission.USER_READ, Scope.ALL)),
])
async def user_list(
    limit: int = 100, offset: int = 0, service: UserService = Depends(deps.get_service(UserService))
):
    """Показать список пользователей."""
    return await service.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=UserProfileRead)
async def user_read(
    pk: int,
    service: UserService = Depends(deps.get_service(UserService)),
    current_user: User = Depends(get_current_user),
):
    """Показать пользователя по id.

    Свой профиль доступен любому пользователю; чужой — только при
    ``USER_READ = ALL`` (админ/менеджер). В свой профиль входят питомцы.
    """
    can_read_any = has(
        current_user.permission_mask, Permission.USER_READ, Scope.ALL
    )
    if current_user.user_id != pk and not can_read_any:
        raise PermissionDeniedError("Можно смотреть только свой профиль")

    user = await service.get(pk)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    return user


@router.post("", response_model=UserRead, dependencies=[
    Depends(deps.require_perm(Permission.USER_WRITE, Scope.ALL)),
])
async def user_create(
    payload: UserCreate,
    service: UserService = Depends(deps.get_service(UserService))
):
    """
    Создать пользователя.
    По умолчанию - CLIENT.
    """
    return await service.create(payload)


@router.put("/{pk}", response_model=UserRead)
async def user_update(
    pk: int,
    payload: UserUpdate,
    service: UserService = Depends(deps.get_service(UserService)),
    rule: PermissionRule = Depends(
        deps.require_perm(
            Permission.USER_WRITE, Scope.OWN, owner_field="user_id"
        )
    ),
):
    """Обновить пользователя.

    Свой профиль может править любая роль; чужой — только при
    ``USER_WRITE = ALL`` (админ).
    """
    user = await service.update(pk, payload, rule=rule)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    return user


@router.put("/{pk}/role", response_model=UserRead, dependencies=[
    Depends(deps.require_role(Role.ADMIN)),
])
async def user_role_update(
    pk: int,
    payload: UserRoleUpdate,
    service: UserService = Depends(deps.get_service(UserService)),
    current_user: User = Depends(get_current_user),
):
    """Назначить роль пользователю. Доступно только администраторам.

    Свою роль менять нельзя, чтобы случайно не оставить систему без админа.
    """
    if current_user.user_id == pk:
        raise PermissionDeniedError("Нельзя менять собственную роль")

    user = await service.update_role(pk, payload.role)
    if user is None:
        raise NotFoundError("Пользователь не найден")
    return user


@router.delete("/{pk}", status_code=204)
async def user_delete(
    pk: int,
    service: UserService = Depends(deps.get_service(UserService)),
    rule: PermissionRule = Depends(
        deps.require_perm(
            Permission.USER_DELETE, Scope.OWN, owner_field="user_id"
        )
    ),
):
    """Удалить пользователя.

    Свой аккаунт может удалить любая роль; чужой — только при
    ``USER_DELETE = ALL`` (админ).
    """
    await service.delete(pk, rule=rule)


# region service

# Роутер без пользовательских зависимостей: сюда пускаем и клиента
# (access-токен), и сервис (service-токен) через ``get_principal``.
router_service = APIRouter(prefix="/users", tags=["users"])


@router_service.get("/{pk}/summary", response_model=Summary)
async def user_summary(
    pk: int, service: UserService = Depends(deps.get_service(UserService)),
    principal: Principal = Depends(get_principal)
):
    """Сводка пользователя (доступна клиенту и сервису).

    Пользователь видит только свою сводку; USER_READ/ALL (админ, менеджер)
    и сервисный токен — любую.
    Для ``pk == 0`` возвращаем «гостевую» сводку: engine использует
    user_id=0 для неавторизованных пользователей TG-бота и не должен
    падать на отсутствующем пользователе.
    """
    if principal.is_user:
        if principal.user is None:
            raise PermissionDeniedError()
        is_self = principal.user.user_id == pk
        can_read_any = has(
            principal.user.permission_mask, Permission.USER_READ, Scope.ALL
        )
        if not is_self and not can_read_any:
            raise PermissionDeniedError("Можно смотреть только свою сводку")

    summary = await service.get_summary_by_id(pk)
    if summary is None:
        if pk == 0:
            return Summary(
                user=UserSummary(id=0, name="Гость", phone=None),
                pets=[],
                notes=None,
            )
        raise NotFoundError("Пользователь не найден")
    return summary

# endregion
