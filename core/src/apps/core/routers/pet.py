"""CRUD для питомцев (Pet).

Путь: /pets*
- GET    /pets              — список
- GET    /pets/{id}         — один элемент
- POST   /pets              — создать
- PUT    /pets/{id}         — обновить
- DELETE /pets/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
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
    limit: int = 100, offset: int = 0, servive: PetService = Depends(deps.get_service(PetService))
):
    """Вернуть список питомцев."""
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=PetRead)
async def pet_read(pk: int, servive: PetService = Depends(deps.get_service(PetService))):
    """Вернуть питомца по id."""
    item = await servive.get(pk)
    if item is None:
        raise NotFoundError("Питомец не найден")
    return item


@router.post("", response_model=PetRead, status_code=201)
async def pet_create(data: PetCreate, servive: PetService = Depends(deps.get_service(PetService))):
    """Создать питомца."""
    return await servive.create(data)


@router.put("/{pk}", response_model=PetRead)
async def pet_update(pk: int, data: PetUpdate, servive: PetService = Depends(deps.get_service(PetService))):
    """Обновить питомца."""
    item = await servive.update(pk, data)
    if item is None:
        raise NotFoundError("Питомец не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def pet_delete(pk: int, servive: PetService = Depends(deps.get_service(PetService))):
    """Удалить питомца."""
    await servive.delete(pk)
