"""CRUD для единиц измерения (Storage).

Путь: /storages*
- GET    /storages              — список
- GET    /storages/{id}         — один элемент
- POST   /storages              — создать
- PUT    /storages/{id}         — обновить
- DELETE /storages/{id}         — удалить

На данной итерации это просто стек наличия на складе с количеством
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.services import StorageService
from src import dependencies as deps
from src.schemas import StorageCreate, StorageRead, StorageUpdate
from src.middleware.auth import get_current_user, bearer_scheme

router = APIRouter(prefix="/storages", tags=["storage"], dependencies=[
    Security(bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[StorageRead])
async def storage_list(
    limit: int = 100, offset: int = 0, servive: StorageService = Depends(deps.get_service(StorageService))
):
    """Вернуть страницу складов."""
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=StorageRead)
async def storage_read(pk: int, servive: StorageService = Depends(deps.get_service(StorageService))):
    """Вернуть склад по id."""
    item = await servive.get(pk)
    if item is None:
        raise NotFoundError("Склад не найден")
    return item


@router.post("", response_model=StorageRead, status_code=201)
async def storage_create(data: StorageCreate, servive: StorageService = Depends(deps.get_service(StorageService))):
    """Создать склад."""
    return await servive.create(data)


@router.put("/{pk}", response_model=StorageRead)
async def storage_update(
    pk: int, data: StorageUpdate, servive: StorageService = Depends(deps.get_service(StorageService))
):
    """Обновить склад."""
    item = await servive.update(pk, data)
    if item is None:
        raise NotFoundError("Склад не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def storage_delete(pk: int, servive: StorageService = Depends(deps.get_service(StorageService))):
    """Удалить склад."""
    await servive.delete(pk)
