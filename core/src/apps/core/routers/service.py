"""CRUD для видов услуг (Service).

Путь: /services*
- GET    /services              — список
- GET    /services/{id}         — один элемент
- POST   /services              — создать
- PUT    /services/{id}         — обновить
- DELETE /services/{id}         — удалить
"""

from fastapi import APIRouter, Depends

from src.services import ServiceService
from src import dependencies as deps
from src.schemas import ServiceCreate, ServiceRead, ServiceUpdate

router = APIRouter(prefix="/services", tags=["services"])


@router.get("", response_model=list[ServiceRead])
async def service_list(
    limit: int = 100, offset: int = 0, uow: ServiceService = Depends(deps.get_uow_factory)
):
    """Вернуть список услуг."""
    return await uow.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=ServiceRead)
async def service_read(pk: int, uow: ServiceService = Depends(deps.get_uow_factory)):
    """Вернуть услугу по id."""
    item = await uow.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Услуга не найдена")
    return item


@router.post("", response_model=ServiceRead, status_code=201)
async def service_create(data: ServiceCreate, uow: ServiceService = Depends(deps.get_uow_factory)):
    """Создать услугу."""
    return await uow.create(data)


@router.put("/{pk}", response_model=ServiceRead)
async def service_update(
    pk: int, data: ServiceUpdate, uow: ServiceService = Depends(deps.get_uow_factory)
):
    """Обновить услугу."""
    item = await uow.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Услуга не найдена")
    return item


@router.delete("/{pk}", status_code=204)
async def service_delete(pk: int, uow: ServiceService = Depends(deps.get_uow_factory)):
    """Удалить услугу."""
    await uow.delete(pk)
