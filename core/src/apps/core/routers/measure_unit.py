"""CRUD для измерений (MeasureUnit).

Путь: /measure-units*
- GET    /measure-units              — список со страницей
- GET    /measure-units/{id}         — один элемент
- POST   /measure-units              — создать
- PUT    /measure-units/{id}         — обновить
- DELETE /measure-units/{id}         — удалить
"""

from fastapi import APIRouter, Depends

from src.services import MeasureUnitService
from src import dependencies as deps
from src.schemas import MeasureUnitCreate, MeasureUnitUpdate, MeasureUnitRead

router = APIRouter("/measure-units", tags=["measure-units"])


@router.get("", response_model=list[MeasureUnitRead])
async def measure_unit_list(
    limit: int = 100,
    offset: int = 0,
    uow: MeasureUnitService = Depends(deps.get_uow_factory),
):
    """Вернуть страницу измерений."""
    return await uow.get_multi(limit=limit, offset=offset)


@router.get("/{pk}", response_model=MeasureUnitRead)
async def measure_unit_read(pk: int, uow: MeasureUnitService = Depends(deps.get_uow_factory)):
    """Вернуть одно измерение по id."""
    item = await uow.get(pk)
    if item is None:
        raise deps.NotFoundError(detail="Измерение не найдено")
    return item


@router.post("", response_model=MeasureUnitRead, status_code=201)
async def measure_unit_create(
    data: MeasureUnitCreate,
    uow: MeasureUnitService = Depends(deps.get_uow_factory),
):
    """Создать новое измерение."""
    return await uow.create(data)


@router.put("/{pk}", response_model=MeasureUnitRead)
async def measure_unit_update(
    pk: int,
    data: MeasureUnitUpdate,
    uow: MeasureUnitService = Depends(deps.get_uow_factory),
):
    """Обновить измерение целиком."""
    item = await uow.update(pk, data)
    if item is None:
        raise deps.NotFoundError(detail="Измерение не найдено")
    return item


@router.delete("/{pk}", status_code=204)
async def measure_unit_delete(pk: int, uow: MeasureUnitService = Depends(deps.get_uow_factory)):
    """Удалить измерение."""
    await uow.delete(pk)
