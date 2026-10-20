"""CRUD для видов животных (PetType).

Путь: /pet-types*
- GET    /pet-types              — список
- GET    /pet-types/{id}         — один элемент
- POST   /pet-types              — создать
- PUT    /pet-types/{id}         — обновить
- DELETE /pet-types/{id}         — удалить
"""

from fastapi import APIRouter, Depends

from src.services import PetTypeService
from src import dependencies as deps
from src.schemas import PetTypeCreate, PetTypeRead, PetTypeUpdate

router = APIRouter("/pet-types", tags=["pet-types"])


@router.get("", response_model=list[PetTypeRead])
async def pet_type_list(
    limit: int = 100, offset: int = 0, uow: PetTypeService = Depends(deps.get_uow_factory)
):
    """Вернуть список видов животных."""
    return await uow.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=PetTypeRead)
async def pet_type_read(pk: int, uow: PetTypeService = Depends(deps.get_uow_factory)):
    """Вернуть вид животного по id."""
    item = await uow.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Вид животного не найден")
    return item


@router.post("", response_model=PetTypeRead, status_code=201)
async def pet_type_create(data: PetTypeCreate, uow: PetTypeService = Depends(deps.get_uow_factory)):
    """Создать вид животного."""
    return await uow.create(data)


@router.put("/{pk}", response_model=PetTypeRead)
async def pet_type_update(
    pk: int, data: PetTypeUpdate, uow: PetTypeService = Depends(deps.get_uow_factory)
):
    """Обновить вид животного."""
    item = await uow.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Вид животного не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def pet_type_delete(pk: int, uow: PetTypeService = Depends(deps.get_uow_factory)):
    """Удалить вид животного."""
    await uow.delete(pk)
