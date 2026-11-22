"""Слоты: генерация сетки и доступность.

Путь: /slots*
- GET  /slots                    — список слотов (с фильтрами)
- GET  /slots/availability       — доступные слоты на период (генерация + пересчёт)
- POST /slots/generate           — явно сгенерировать сетку на период
- GET  /slots/{id}               — один слот
"""

from datetime import date

from fastapi import APIRouter, Depends

from src.excpetions.crud import NotFoundError
from src.models.enums.slot_status import SlotStatus
from src.services import SlotService
from src import dependencies as deps
from src.schemas import (
    SlotGenerateRequest,
    SlotGenerateResponse,
    SlotRead,
)
from src.middleware.mix_scheme import get_principal

# Read/write слотов доступны и пользователю, и сервисному токену
# (будущая интеграция: Яндекс/бот). get_principal принимает оба типа токена.
router = APIRouter(prefix="/slots", tags=["slots"], dependencies=[
    Depends(get_principal),
])


@router.get("", response_model=list[SlotRead])
async def slot_list(
    resource_id: int | None = None,
    service_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: SlotStatus | None = None,
    limit: int = 100,
    offset: int = 0,
    service: SlotService = Depends(deps.get_service(SlotService)),
):
    """Вернуть сохранённые слоты с фильтрами."""
    return await service.get_multi(
        resource_id=resource_id,
        service_id=service_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.get("/availability", response_model=list[SlotRead])
async def slot_availability(
    resource_id: int,
    service_id: int,
    date_from: date,
    date_to: date,
    step_minutes: int | None = None,
    only_available: bool = False,
    limit: int = 500,
    offset: int = 0,
    service: SlotService = Depends(deps.get_service(SlotService)),
):
    """Доступность мастера по услуге на период.

    Слоты генерируются по графику (идемпотентно), затем статусы пересчитываются
    по активным бронированиям. ``available=true`` — слот можно бронировать.
    """
    return await service.list_availability(
        resource_id=resource_id,
        service_id=service_id,
        date_from=date_from,
        date_to=date_to,
        step_minutes=step_minutes,
        only_available=only_available,
        limit=limit,
        offset=offset,
    )


@router.post("/generate", response_model=SlotGenerateResponse)
async def slot_generate(
    data: SlotGenerateRequest,
    service: SlotService = Depends(deps.get_service(SlotService)),
):
    """Сгенерировать сетку слотов на период."""
    created, slots = await service.generate(data)
    return SlotGenerateResponse(
        created=created,
        slots=[SlotRead.model_validate(slot) for slot in slots],
    )


@router.get("/{pk}", response_model=SlotRead)
async def slot_read(
    pk: int,
    service: SlotService = Depends(deps.get_service(SlotService)),
):
    """Вернуть слот по id."""
    item = await service.get(pk)
    if item is None:
        raise NotFoundError("Слот не найден")
    return item
