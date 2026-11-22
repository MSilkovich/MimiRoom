from src.excpetions.crud import ConflictError
from src.models.work_schedule import WorkSchedule
from src.schemas import WorkScheduleCreate, WorkScheduleUpdate
from .base import BaseService


class WorkScheduleService(
    BaseService[WorkSchedule, WorkScheduleCreate, WorkScheduleUpdate]
):
    model = WorkSchedule

    async def create(self, data: WorkScheduleCreate) -> WorkSchedule:
        async with self.uow_factory() as uow:
            repo = uow.repository(WorkSchedule)
            existing = await repo.get_single(
                resource_id=data.resource_id, weekday=data.weekday
            )
            if existing is not None:
                raise ConflictError(
                    "Для мастера уже задан график на этот день недели"
                )
            instance = await repo.create(data.model_dump())
            await uow.commit()
            return instance

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        rule=None,
        resource_id: int | None = None,
    ) -> list[WorkSchedule]:
        filters: dict = {}
        if resource_id is not None:
            filters["resource_id"] = resource_id
        async with self.uow_factory() as uow:
            repo = uow.repository(WorkSchedule)
            return await repo.get_multi(
                order=order, limit=limit, offset=offset, **filters
            )
