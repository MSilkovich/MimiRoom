"""CRUD для питомцев (Pet).

Путь: /pets*
- GET    /pets              — список
- GET    /pets/{id}         — один элемент
- POST   /pets              — создать
- PUT    /pets/{id}         — обновить
- DELETE /pets/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.services import PetService
from src import dependencies as deps
from src.schemas import PetCreate, PetRead, PetUpdate
from src.middleware.auth import get_current_user, bearer_scheme


router = APIRouter(prefix="/pets", tags=["pets"], dependencies=[
    Security(bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[PetRead])
async def pet_list(
    limit: int = 100, offset: int = 0, uow: PetService = Depends(deps.get_uow_factory)
):
    """Вернуть список питомцев."""
    return await uow.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=PetRead)
async def pet_read(pk: int, uow: PetService = Depends(deps.get_uow_factory)):
    """Вернуть питомца по id."""
    item = await uow.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Питомец не найден")
    return item


@router.post("", response_model=PetRead, status_code=201)
async def pet_create(data: PetCreate, uow: PetService = Depends(deps.get_uow_factory)):
    """Создать питомца."""
    return await uow.create(data)


@router.put("/{pk}", response_model=PetRead)
async def pet_update(pk: int, data: PetUpdate, uow: PetService = Depends(deps.get_uow_factory)):
    """Обновить питомца."""
    item = await uow.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Питомец не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def pet_delete(pk: int, uow: PetService = Depends(deps.get_uow_factory)):
    """Удалить питомца."""
    await uow.delete(pk)
