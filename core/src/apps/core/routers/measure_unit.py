"""CRUD для измерений (MeasureUnit).

Путь: /measure-units*
- GET    /measure-units              — список со страницей
- GET    /measure-units/{id}         — один элемент
- POST   /measure-units              — создать
- PUT    /measure-units/{id}         — обновить
- DELETE /measure-units/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.permissions.enums.permissions import Permission
from src.permissions.enums.scope import Scope
from src.permissions.permission_rule import PermissionRule
from src.middleware.auth import get_current_user, bearer_scheme
from src.services import MeasureUnitService
from src import dependencies as deps
from src.schemas import MeasureUnitCreate, MeasureUnitUpdate, MeasureUnitRead

router = APIRouter(prefix="/measure-units", tags=["measure-units"], dependencies=[
    Security(bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[MeasureUnitRead])
async def measure_unit_list(
    limit: int = 100,
    offset: int = 0,
    servive: MeasureUnitService = Depends(deps.get_service(MeasureUnitService))
):
    """Вернуть страницу измерений."""
    return await servive.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=MeasureUnitRead)
async def measure_unit_read(pk: int, servive: MeasureUnitService = Depends(deps.get_service(MeasureUnitService))):
    """Вернуть одно измерение по id."""
    item = await servive.get(pk)
    if item is None:
        raise NotFoundError("Измерение не найдено")
    return item


@router.post("", response_model=MeasureUnitRead, status_code=201)
async def measure_unit_create(
    data: MeasureUnitCreate,
    servive: MeasureUnitService = Depends(deps.get_service(MeasureUnitService))
):
    """Создать новое измерение."""
    return await servive.create(data)


@router.put("/{pk}", response_model=MeasureUnitRead)
async def measure_unit_update(
    pk: int,
    data: MeasureUnitUpdate,
    servive: MeasureUnitService = Depends(deps.get_service(MeasureUnitService))
):
    """Обновить измерение целиком."""
    item = await servive.update(pk, data)
    if item is None:
        raise NotFoundError("Измерение не найдено")
    return item


@router.delete("/{pk}", status_code=204)
async def measure_unit_delete(
    pk: int,
    servive: MeasureUnitService = Depends(
        deps.get_service(MeasureUnitService)),
    rule: PermissionRule = Depends(deps.require_perm(
        Permission.PET_DELETE, Scope.OWN))  # WARNING: !!! другой perm
):
    """Удалить измерение."""
    await servive.delete(pk)
