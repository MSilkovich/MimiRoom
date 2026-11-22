"""CRUD для графика работы мастеров (WorkSchedule).

Путь: /work-schedules*
- GET    /work-schedules              — список (можно отфильтровать по master_id)
- GET    /work-schedules/{id}         — один элемент
- POST   /work-schedules              — создать
- PUT    /work-schedules/{id}         — обновить
- DELETE /work-schedules/{id}         — удалить
"""

from fastapi import APIRouter, Depends, Security

from src.excpetions.crud import NotFoundError
from src.services import WorkScheduleService
from src import dependencies as deps
from src.schemas import (
    WorkScheduleCreate,
    WorkScheduleRead,
    WorkScheduleUpdate,
)
from src.middleware.auth import get_current_user, auth_bearer_scheme

router = APIRouter(prefix="/work-schedules", tags=["work-schedules"], dependencies=[
    Security(auth_bearer_scheme),
    Depends(get_current_user),
])


@router.get("", response_model=list[WorkScheduleRead])
async def work_schedule_list(
    master_id: int | None = None,
    limit: int = 100,
    offset: int = 0,
    service: WorkScheduleService = Depends(
        deps.get_service(WorkScheduleService)
    ),
):
    """Вернуть графики работы (опционально — только одного мастера)."""
    return await service.get_multi(
        limit=limit, offset=offset, master_id=master_id
    )


@router.get("/{pk}", response_model=WorkScheduleRead)
async def work_schedule_read(
    pk: int,
    service: WorkScheduleService = Depends(
        deps.get_service(WorkScheduleService)
    ),
):
    """Вернуть график по id."""
    item = await service.get(pk)
    if item is None:
        raise NotFoundError("График не найден")
    return item


@router.post("", response_model=WorkScheduleRead, status_code=201)
async def work_schedule_create(
    data: WorkScheduleCreate,
    service: WorkScheduleService = Depends(
        deps.get_service(WorkScheduleService)
    ),
):
    """Создать график на день недели."""
    return await service.create(data)


@router.put("/{pk}", response_model=WorkScheduleRead)
async def work_schedule_update(
    pk: int,
    data: WorkScheduleUpdate,
    service: WorkScheduleService = Depends(
        deps.get_service(WorkScheduleService)
    ),
):
    """Обновить график."""
    item = await service.update(pk, data)
    if item is None:
        raise NotFoundError("График не найден")
    return item


@router.delete("/{pk}", status_code=204)
async def work_schedule_delete(
    pk: int,
    service: WorkScheduleService = Depends(
        deps.get_service(WorkScheduleService)
    ),
):
    """Удалить график."""
    await service.delete(pk)
