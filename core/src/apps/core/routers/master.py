"""CRUD для мастеров (bookable users).

Путь: /masters*
- GET    /masters              — список мастеров
- GET    /masters/{id}         — один мастер
- POST   /masters              — создать мастера (= пользователь role=groomer)
- PUT    /masters/{id}         — обновить мастера
- DELETE /masters/{id}         — удалить мастера
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.permissions.enums.permissions import Permission
from src.permissions.enums.scope import Scope
from src.permissions.permission_rule import PermissionRule
from src.services import MasterService
from src import dependencies as deps
from src.schemas import MasterCreate, MasterRead, MasterUpdate
from src.middleware.auth import get_current_user, auth_bearer_scheme

router = APIRouter(prefix="/masters", tags=["masters"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[MasterRead], dependencies=[
    Depends(deps.require_perm(Permission.MASTER_READ, Scope.ALL)),
])
async def master_list(
    limit: int = 100,
    offset: int = 0,
    service: MasterService = Depends(deps.get_service(MasterService)),
):
    """Вернуть список мастеров."""
    return await service.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=MasterRead, dependencies=[
    Depends(deps.require_perm(Permission.MASTER_READ, Scope.ALL)),
])
async def master_read(
    pk: int,
    service: MasterService = Depends(deps.get_service(MasterService)),
):
    """Вернуть мастера по id."""
    item = await service.get(pk)
    if item is None:
        raise NotFoundError("Мастер не найден")
    return item


@router.post("", response_model=MasterRead, status_code=201, dependencies=[
    Depends(deps.require_perm(Permission.MASTER_WRITE, Scope.ALL)),
])
async def master_create(
    data: MasterCreate,
    service: MasterService = Depends(deps.get_service(MasterService)),
):
    """Создать мастера (можно сразу привязать услуги)."""
    return await service.create(data)


@router.put("/{pk}", response_model=MasterRead)
async def master_update(
    pk: int,
    data: MasterUpdate,
    service: MasterService = Depends(deps.get_service(MasterService)),
    rule: PermissionRule = Depends(
        deps.require_perm(
            Permission.MASTER_WRITE, Scope.OWN, owner_field="user_id"
        )
    ),
):
    """Обновить мастера.

    Грумер может редактировать только свой профиль; менеджер/админ — любой.
    """
    item = await service.update(pk, data, rule=rule)
    if item is None:
        raise NotFoundError("Мастер не найден")
    return item


@router.delete("/{pk}", status_code=204, dependencies=[
    Depends(deps.require_perm(Permission.MASTER_DELETE, Scope.ALL)),
])
async def master_delete(
    pk: int,
    service: MasterService = Depends(deps.get_service(MasterService)),
):
    """Удалить мастера."""
    await service.delete(pk)


# region service

# read-only список мастеров для сервисных токенов (бот/будущая интеграция)
router_service = APIRouter(
    prefix="/s/masters",
    include_in_schema=False,
    dependencies=[Depends(deps.require_service)],
)


@router_service.get("", response_model=list[MasterRead])
async def master_list_service(
    limit: int = 100,
    offset: int = 0,
    service: MasterService = Depends(deps.get_service(MasterService)),
):
    """Вернуть список мастеров (только service-токен)."""
    return await service.get_multi(limit=limit, offset=offset)

# endregion
