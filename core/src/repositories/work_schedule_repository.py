from ..models.work_schedule import WorkSchedule
from .sqlalchemy_repository import SqlAlchemyRepository


class WorkScheduleRepository(SqlAlchemyRepository[WorkSchedule]):
    def __init__(self, session):
        super().__init__(WorkSchedule, session)

    async def get_for_master(self, master_id: int) -> list[WorkSchedule]:
        """Все графики мастера (по одному на день недели)."""
        return await self.get_multi(
            master_id=master_id,
            order="work_schedule_id",
        )
