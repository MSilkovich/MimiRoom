"""CRUD для пород (Breed).

Путь: /breeds*
- GET    /breeds              — список
- GET    /breeds/{id}         — один элемент
- POST   /breeds              — создать
- PUT    /breeds/{id}         — обновить
- DELETE /breeds/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.permissions.enums.permissions import Permission
from src.permissions.enums.scope import Scope
from src.services import BreedService
from src import dependencies as deps
from src.schemas import BreedCreate, BreedRead, BreedUpdate
from src.middleware.auth import get_current_user, auth_bearer_scheme

router = APIRouter(prefix="/breeds", tags=["breeds"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[BreedRead], dependencies=[
    Depends(deps.require_perm(Permission.DICTIONARIES_READ, Scope.ALL)),
])
async def breed_list(
    limit: int = 100, offset: int = 0, servive: BreedService = Depends(deps.get_service(BreedService))
):
    """Вернуть список пород."""
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=BreedRead, dependencies=[
    Depends(deps.require_perm(Permission.DICTIONARIES_READ, Scope.ALL)),
])
async def breed_read(pk: int, servive: BreedService = Depends(deps.get_service(BreedService))):
    """Вернуть породу по id."""
    item = await servive.get(pk)
    if item is None:
        raise NotFoundError("Порода не найдена")
    return item


@router.post("", response_model=BreedRead, status_code=201, dependencies=[
    Depends(deps.require_perm(Permission.DICTIONARIES_WRITE, Scope.ALL)),
])
async def breed_create(data: BreedCreate, servive: BreedService = Depends(deps.get_service(BreedService))):
    """Создать породу."""
    return await servive.create(data)


@router.put("/{pk}", response_model=BreedRead, dependencies=[
    Depends(deps.require_perm(Permission.DICTIONARIES_WRITE, Scope.ALL)),
])
async def breed_update(pk: int, data: BreedUpdate, servive: BreedService = Depends(deps.get_service(BreedService))):
    """Обновить породу."""
    item = await servive.update(pk, data)
    if item is None:
        raise NotFoundError("Порода не найдена")
    return item


@router.delete("/{pk}", status_code=204, dependencies=[
    Depends(deps.require_perm(Permission.DICTIONARIES_DELETE, Scope.ALL)),
])
async def breed_delete(pk: int, servive: BreedService = Depends(deps.get_service(BreedService))):
    """Удалить породу."""
    await servive.delete(pk)
