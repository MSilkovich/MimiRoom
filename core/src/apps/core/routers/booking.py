"""Бронирования (Booking) — запись на конкретное время.

Путь: /bookings*
- GET    /bookings              — список (фильтры: master_id, client_id, status, date_from, date_to)
- GET    /bookings/{id}         — одно бронирование
- POST   /bookings              — создать на конкретное время
- PUT    /bookings/{id}         — обновить
- POST   /bookings/{id}/cancel  — отменить
- POST   /bookings/{id}/complete — отметить выполненным
- DELETE /bookings/{id}         — удалить
"""

from datetime import date

from fastapi import APIRouter, Depends

from src.excpetions.crud import NotFoundError
from src.models.enums.booking_status import BookingStatus
from src.services import BookingService
from src import dependencies as deps
from src.schemas import BookingCreate, BookingRead, BookingUpdate
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.get("", response_model=list[BookingRead])
async def booking_list(
    master_id: int | None = None,
    client_id: int | None = None,
    status: BookingStatus | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
    offset: int = 0,
    service: BookingService = Depends(deps.get_service(BookingService)),
    principal: Principal = Depends(get_principal),
):
    """Вернуть список бронирований.

    ``date_from``/``date_to`` — включительный диапазон дат по ``start_time``
    (в таймзоне салона). Оба параметра необязательны.
    """
    return await service.get_multi(
        limit=limit,
        offset=offset,
        master_id=master_id,
        client_id=client_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
    )


@router.get("/{pk}", response_model=BookingRead)
async def booking_read(
    pk: int,
    service: BookingService = Depends(deps.get_service(BookingService)),
    principal: Principal = Depends(get_principal),
):
    """Вернуть бронирование по id."""
    item = await service.get(pk)
    if item is None:
        raise NotFoundError("Бронирование не найдено")
    return item


@router.post("", response_model=BookingRead, status_code=201)
async def booking_create(
    data: BookingCreate,
    service: BookingService = Depends(deps.get_service(BookingService)),
    principal: Principal = Depends(get_principal),
):
    """Создать бронирование на конкретное время.

    Сервер валидирует график мастера, сетку слотов и пересечения интервалов
    (с учётом буферов услуг). Конкурентные запросы на пересекающееся время
    защищены advisory-lock по мастеру.
    """
    return await service.create(data)


@router.put("/{pk}", response_model=BookingRead)
async def booking_update(
    pk: int,
    data: BookingUpdate,
    service: BookingService = Depends(deps.get_service(BookingService)),
    principal: Principal = Depends(get_principal),
):
    """Обновить бронирование (в т.ч. сменить статус)."""
    item = await service.update(pk, data)
    if item is None:
        raise NotFoundError("Бронирование не найдено")
    return item


@router.post("/{pk}/cancel", response_model=BookingRead)
async def booking_cancel(
    pk: int,
    service: BookingService = Depends(deps.get_service(BookingService)),
    principal: Principal = Depends(get_principal),
):
    """Отменить бронирование — время снова станет доступным."""
    return await service.cancel(pk)


@router.post("/{pk}/complete", response_model=BookingRead)
async def booking_complete(
    pk: int,
    service: BookingService = Depends(deps.get_service(BookingService)),
    principal: Principal = Depends(get_principal),
):
    """Отметить визит выполненным (статус ``completed``)."""
    return await service.complete(pk)


@router.delete("/{pk}", status_code=204)
async def booking_delete(
    pk: int,
    service: BookingService = Depends(deps.get_service(BookingService)),
    principal: Principal = Depends(get_principal),
):
    """Удалить бронирование."""
    await service.delete(pk)
