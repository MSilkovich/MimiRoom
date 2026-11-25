"""CRUD для питомцев (Pet).

Путь: /pets*
- GET    /pets              — список
- GET    /pets/{id}         — один элемент
- GET    /pets/{id}/history — история посещений питомца
- POST   /pets              — создать
- PUT    /pets/{id}         — обновить
- DELETE /pets/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.models.enums.booking_status import BookingStatus
from src.permissions.enums.permissions import Permission
from src.permissions.enums.scope import Scope
from src.permissions.permission_rule import PermissionRule
from src.services import PetService
from src import dependencies as deps
from src.schemas import PetCreate, PetHistoryRead, PetRead, PetUpdate
from src.middleware.auth import get_current_user, auth_bearer_scheme


router = APIRouter(prefix="/pets", tags=["pets"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[PetRead])
async def pet_list(
    limit: int = 100,
    offset: int = 0,
    servive: PetService = Depends(deps.get_service(PetService)),
    rule: PermissionRule = Depends(
        deps.require_perm(Permission.PET_READ, Scope.OWN, owner_field="owner_id")
    ),
):
    """Вернуть список питомцев (клиент — только своих)."""
    return await servive.get_multi(limit=limit, offset=offset, rule=rule)


@router.get("/{pk}", response_model=PetRead)
async def pet_read(
    pk: int,
    servive: PetService = Depends(deps.get_service(PetService)),
    rule: PermissionRule = Depends(
        deps.require_perm(Permission.PET_READ, Scope.OWN, owner_field="owner_id")
    ),
):
    """Вернуть питомца по id (клиент — только своего)."""
    item = await servive.get(pk, rule=rule)
    if item is None:
        raise NotFoundError("Питомец не найден")
    return item


@router.get("/{pk}/history", response_model=list[PetHistoryRead])
async def pet_history(
    pk: int,
    status: BookingStatus | None = None,
    limit: int = 100,
    offset: int = 0,
    service: PetService = Depends(deps.get_service(PetService)),
    rule: PermissionRule = Depends(
        deps.require_perm(Permission.PET_READ, Scope.OWN, owner_field="owner_id")
    ),
):
    """Вернуть историю посещений питомца (все брони, новые сверху)."""
    return await service.get_history(
        pk, status=status, limit=limit, offset=offset, rule=rule
    )


@router.post("", response_model=PetRead, status_code=201)
async def pet_create(
    data: PetCreate,
    servive: PetService = Depends(deps.get_service(PetService)),
    rule: PermissionRule = Depends(
        deps.require_perm(Permission.PET_WRITE, Scope.OWN, owner_field="owner_id")
    ),
):
    """Создать питомца (клиент — только себе)."""
    return await servive.create(data, rule=rule)


@router.put("/{pk}", response_model=PetRead)
async def pet_update(
    pk: int,
    data: PetUpdate,
    servive: PetService = Depends(deps.get_service(PetService)),
    rule: PermissionRule = Depends(
        deps.require_perm(Permission.PET_WRITE, Scope.OWN, owner_field="owner_id")
    ),
):
    """Обновить питомца (клиент — только своего)."""
    item = await servive.update(pk, data, rule=rule)
    if item is None:
        raise NotFoundError("Питомец не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def pet_delete(
    pk: int,
    servive: PetService = Depends(deps.get_service(PetService)),
    rule: PermissionRule = Depends(
        deps.require_perm(Permission.PET_DELETE, Scope.OWN, owner_field="owner_id")
    ),
):
    """Удалить питомца (клиент — только своего)."""
    await servive.delete(pk, rule=rule)
