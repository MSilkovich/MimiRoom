"""CRUD для видов услуг (Service).

Путь: /services*
- GET    /services              — список
- GET    /services/{id}         — один элемент
- POST   /services              — создать
- PUT    /services/{id}         — обновить
- DELETE /services/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.permissions.enums.permissions import Permission
from src.permissions.enums.scope import Scope
from src.services import ServiceService
from src import dependencies as deps
from src.schemas import ServiceCreate, ServiceRead, ServiceUpdate
from src.middleware.auth import get_current_user, auth_bearer_scheme

router = APIRouter(prefix="/services", tags=["services"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[ServiceRead], dependencies=[
    Depends(deps.require_perm(Permission.SERVICE_READ, Scope.ALL)),
])
async def service_list(
    limit: int = 100, offset: int = 0, servive: ServiceService = Depends(deps.get_service(ServiceService))
):
    """Вернуть список услуг."""
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=ServiceRead, dependencies=[
    Depends(deps.require_perm(Permission.SERVICE_READ, Scope.ALL)),
])
async def service_read(pk: int, servive: ServiceService = Depends(deps.get_service(ServiceService))):
    """Вернуть услугу по id."""
    item = await servive.get(pk)
    if item is None:
        raise NotFoundError("Услуга не найдена")
    return item


@router.post("", response_model=ServiceRead, status_code=201, dependencies=[
    Depends(deps.require_perm(Permission.SERVICE_WRITE, Scope.ALL)),
])
async def service_create(data: ServiceCreate, servive: ServiceService = Depends(deps.get_service(ServiceService))):
    """Создать услугу."""
    return await servive.create(data)


@router.put("/{pk}", response_model=ServiceRead, dependencies=[
    Depends(deps.require_perm(Permission.SERVICE_WRITE, Scope.ALL)),
])
async def service_update(
    pk: int, data: ServiceUpdate, servive: ServiceService = Depends(deps.get_service(ServiceService))
):
    """Обновить услугу."""
    item = await servive.update(pk, data)
    if item is None:
        raise NotFoundError("Услуга не найдена")
    return item


@router.delete("/{pk}", status_code=204, dependencies=[
    Depends(deps.require_perm(Permission.SERVICE_DELETE, Scope.ALL)),
])
async def service_delete(pk: int, servive: ServiceService = Depends(deps.get_service(ServiceService))):
    """Удалить услугу."""
    await servive.delete(pk)

# region service

# WARNING: костыль
router_service = APIRouter(
    prefix="/s/services",
    include_in_schema=False,
    dependencies=[Depends(deps.require_service)],
)


@router_service.get("", response_model=list[ServiceRead], include_in_schema=False)
async def service_list_service(
    limit: int = 100, offset: int = 0, servive: ServiceService = Depends(deps.get_service(ServiceService)),
):
    """Вернуть список услуг (только service-токен)."""
    return await servive.get_multi(limit=limit, offset=offset)

# endregion
