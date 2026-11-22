from ..models.work_schedule import WorkSchedule
from .sqlalchemy_repository import SqlAlchemyRepository


class WorkScheduleRepository(SqlAlchemyRepository[WorkSchedule]):
    def __init__(self, session):
        super().__init__(WorkSchedule, session)

    async def get_for_resource(self, resource_id: int) -> list[WorkSchedule]:
        """Все графики мастера (по одному на день недели)."""
        return await self.get_multi(
            resource_id=resource_id,
            order="work_schedule_id",
        )
