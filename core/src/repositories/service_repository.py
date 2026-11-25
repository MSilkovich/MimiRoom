from sqlalchemy import delete, select

from ..context import get_current_user
from ..models.master_service import MasterService as MasterServiceLink
from ..models.service import Service
from .sqlalchemy_repository import SqlAlchemyRepository


class ServiceRepository(SqlAlchemyRepository[Service]):
    def __init__(self, session):
        super().__init__(Service, session)

    async def replace_masters(
        self, service_id: int, master_ids: list[int]
    ) -> None:
        """Полностью переписать набор мастеров, оказывающих услугу."""
        await self.session.execute(
            delete(MasterServiceLink).where(
                MasterServiceLink.service_id == service_id
            )
        )
        user = get_current_user()
        user_id = user.user_id if user is not None else 0
        for master_id in dict.fromkeys(master_ids):
            self.session.add(
                MasterServiceLink(
                    master_id=master_id,
                    service_id=service_id,
                    who_create=user_id,
                    who_update=user_id,
                )
            )
        await self.session.flush()

    async def get_master_ids(self, service_id: int) -> set[int]:
        rows = await self.session.execute(
            select(MasterServiceLink.master_id).where(
                MasterServiceLink.service_id == service_id
            )
        )
        return set(rows.scalars().all())
