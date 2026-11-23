"""Слоты — расчёт доступного времени и административный интервал.

Слоты **не хранятся** в БД: они рассчитываются на лету из графика мастера,
длительности/буферов услуги и активных броней.

Путь: /slots*
- POST /slots/available   — свободные слоты под услугу/мастера/период (тело);
- GET  /slots/interval    — текущий шаг сетки слотов;
- POST /slots/interval    — задать шаг сетки (администратор).
"""

from fastapi import APIRouter, Depends

from src.excpetions.auth import PermissionDeniedError
from src.permissions.enums.roles import Role
from src.services import SlotService
from src import dependencies as deps
from src.schemas import (
    SlotIntervalRead,
    SlotIntervalUpdate,
    SlotRead,
    SlotsAvailableRequest,
)
from src.middleware.mix_scheme import get_principal
from src.middleware.principal import Principal

# Чтение доступности — и пользователю, и сервисному токену (бот/интеграция).
router = APIRouter(prefix="/slots", tags=["slots"], dependencies=[
    Depends(get_principal),
])


def _require_admin(principal: Principal) -> None:
    """Настройки сетки меняет только администратор/менеджер."""
    if (
        not principal.is_user
        or principal.user is None
        or principal.user.role not in (Role.ADMIN, Role.MANAGER)
    ):
        raise PermissionDeniedError("Менять интервал слотов может администратор")


@router.post("/available", response_model=list[SlotRead])
async def slots_available(
    data: SlotsAvailableRequest,
    service: SlotService = Depends(deps.get_service(SlotService)),
):
    """Рассчитать свободные слоты.

    Параметры передаются в теле запроса (не в query). Если ``master_id`` не
    задан — мастера подбирает сервер (см. ``select_master_for_day``).
    """
    return await service.list_available(data)


@router.get("/interval", response_model=SlotIntervalRead)
async def slot_interval_get(
    service: SlotService = Depends(deps.get_service(SlotService)),
):
    """Вернуть текущий шаг сетки слотов (минуты)."""
    return SlotIntervalRead(interval_minutes=await service.get_interval())


@router.post("/interval", response_model=SlotIntervalRead)
async def slot_interval_set(
    data: SlotIntervalUpdate,
    service: SlotService = Depends(deps.get_service(SlotService)),
    principal: Principal = Depends(get_principal),
):
    """Задать шаг сетки слотов (например, 30 минут). Только администратор."""
    _require_admin(principal)
    value = await service.set_interval(data.interval_minutes)
    return SlotIntervalRead(interval_minutes=value)
