"""CRUD для мастеров/исполнителей (Resource).

Путь: /resources*
- GET    /resources              — список
- GET    /resources/{id}         — один элемент
- POST   /resources              — создать
- PUT    /resources/{id}         — обновить
- DELETE /resources/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.services import ResourceService
from src import dependencies as deps
from src.schemas import ResourceCreate, ResourceRead, ResourceUpdate
from src.middleware.auth import get_current_user, auth_bearer_scheme
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal

router = APIRouter(prefix="/resources", tags=["resources"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[ResourceRead])
async def resource_list(
    limit: int = 100,
    offset: int = 0,
    service: ResourceService = Depends(deps.get_service(ResourceService)),
):
    """Вернуть список мастеров."""
    return await service.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=ResourceRead)
async def resource_read(
    pk: int,
    service: ResourceService = Depends(deps.get_service(ResourceService)),
):
    """Вернуть мастера по id."""
    item = await service.get(pk)
    if item is None:
        raise NotFoundError("Мастер не найден")
    return item


@router.post("", response_model=ResourceRead, status_code=201)
async def resource_create(
    data: ResourceCreate,
    service: ResourceService = Depends(deps.get_service(ResourceService)),
):
    """Создать мастера (можно сразу привязать услуги)."""
    return await service.create(data)


@router.put("/{pk}", response_model=ResourceRead)
async def resource_update(
    pk: int,
    data: ResourceUpdate,
    service: ResourceService = Depends(deps.get_service(ResourceService)),
):
    """Обновить мастера."""
    item = await service.update(pk, data)
    if item is None:
        raise NotFoundError("Мастер не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def resource_delete(
    pk: int,
    service: ResourceService = Depends(deps.get_service(ResourceService)),
):
    """Удалить мастера."""
    await service.delete(pk)


# region service

# WARNING: костыль (как и /s/services) — read-only список мастеров для
# сервисных токенов (бот/будущая интеграция), без схемы в openapi.
router_service = APIRouter(prefix="/s/resources", include_in_schema=False)


@router_service.get("", response_model=list[ResourceRead])
async def resource_list_service(
    limit: int = 100,
    offset: int = 0,
    service: ResourceService = Depends(deps.get_service(ResourceService)),
    principal: Principal = Depends(get_principal),
):
    """Вернуть список мастеров (для сервисных токенов)."""
    return await service.get_multi(limit=limit, offset=offset)

# endregion
