"""CRUD для видов животных (PetType).

Путь: /pet-types*
- GET    /pet-types              — список
- GET    /pet-types/{id}         — один элемент
- POST   /pet-types              — создать
- PUT    /pet-types/{id}         — обновить
- DELETE /pet-types/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.services import PetTypeService
from src import dependencies as deps
from src.schemas import PetTypeCreate, PetTypeRead, PetTypeUpdate
from src.middleware.auth import get_current_user, bearer_scheme


router = APIRouter(prefix="/pet-types", tags=["pet-types"], dependencies=[
    Security(bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[PetTypeRead])
async def pet_type_list(
    limit: int = 100, offset: int = 0, servive: PetTypeService = Depends(deps.get_service(PetTypeService))
):
    """Вернуть список видов животных."""
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=PetTypeRead)
async def pet_type_read(pk: int, servive: PetTypeService = Depends(deps.get_service(PetTypeService))):
    """Вернуть вид животного по id."""
    item = await servive.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Вид животного не найден")
    return item


@router.post("", response_model=PetTypeRead, status_code=201)
async def pet_type_create(data: PetTypeCreate, servive: PetTypeService = Depends(deps.get_service(PetTypeService))):
    """Создать вид животного."""
    return await servive.create(data)


@router.put("/{pk}", response_model=PetTypeRead)
async def pet_type_update(
    pk: int, data: PetTypeUpdate, servive: PetTypeService = Depends(deps.get_service(PetTypeService))
):
    """Обновить вид животного."""
    item = await servive.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Вид животного не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def pet_type_delete(pk: int, servive: PetTypeService = Depends(deps.get_service(PetTypeService))):
    """Удалить вид животного."""
    await servive.delete(pk)
