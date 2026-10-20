"""CRUD для видов пород (Breed).

Путь: /breeds*
- GET    /breeds              — список
- GET    /breeds/{id}         — один элемент
- POST   /breeds              — создать
- PUT    /breeds/{id}         — обновить
- DELETE /breeds/{id}         — удалить
"""

from fastapi import APIRouter, Depends

from src.services import BreedService
from src import dependencies as deps
from src.schemas import BreedCreate, BreedRead, BreedUpdate

router = APIRouter("/breeds", tags=["breeds"])


@router.get("", response_model=list[BreedRead])
async def breed_list(
    limit: int = 100, offset: int = 0, uow: BreedService = Depends(deps.get_uow_factory)
):
    """Вернуть список пород."""
    return await uow.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=BreedRead)
async def breed_read(pk: int, uow: BreedService = Depends(deps.get_uow_factory)):
    """Вернуть породу по id."""
    item = await uow.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Порода не найдена")
    return item


@router.post("", response_model=BreedRead, status_code=201)
async def breed_create(data: BreedCreate, uow: BreedService = Depends(deps.get_uow_factory)):
    """Создать породу."""
    return await uow.create(data)


@router.put("/{pk}", response_model=BreedRead)
async def breed_update(pk: int, data: BreedUpdate, uow: BreedService = Depends(deps.get_uow_factory)):
    """Обновить породу."""
    item = await uow.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Порода не найдена")
    return item


@router.delete("/{pk}", status_code=204)
async def breed_delete(pk: int, uow: BreedService = Depends(deps.get_uow_factory)):
    """Удалить породу."""
    await uow.delete(pk)
