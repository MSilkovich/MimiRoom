"""CRUD для единиц измерения (Storage).

Путь: /storages*
- GET    /storages              — список
- GET    /storages/{id}         — один элемент
- POST   /storages              — создать
- PUT    /storages/{id}         — обновить
- DELETE /storages/{id}         — удалить
"""

from fastapi import APIRouter, Depends

from src.services import StorageService
from src import dependencies as deps
from src.schemas import StorageCreate, StorageRead, StorageUpdate

router = APIRouter(prefix="/storages", tags=["storage"])


@router.get("", response_model=list[StorageRead])
async def storage_list(
    limit: int = 100, offset: int = 0, uow: StorageService = Depends(deps.get_uow_factory)
):
    """Вернуть страницу складов."""
    return await uow.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=StorageRead)
async def storage_read(pk: int, uow: StorageService = Depends(deps.get_uow_factory)):
    """Вернуть склад по id."""
    item = await uow.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Склад не найден")
    return item


@router.post("", response_model=StorageRead, status_code=201)
async def storage_create(data: StorageCreate, uow: StorageService = Depends(deps.get_uow_factory)):
    """Создать склад."""
    return await uow.create(data)


@router.put("/{pk}", response_model=StorageRead)
async def storage_update(
    pk: int, data: StorageUpdate, uow: StorageService = Depends(deps.get_uow_factory)
):
    """Обновить склад."""
    item = await uow.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Склад не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def storage_delete(pk: int, uow: StorageService = Depends(deps.get_uow_factory)):
    """Удалить склад."""
    await uow.delete(pk)
