from sqlalchemy import delete, insert, select

from ..models.resource import resource_services
from ..models.service import Service
from .sqlalchemy_repository import SqlAlchemyRepository


class ServiceRepository(SqlAlchemyRepository[Service]):
    def __init__(self, session):
        super().__init__(Service, session)

    async def replace_resources(
        self, service_id: int, resource_ids: list[int]
    ) -> None:
        """Полностью переписать набор мастеров, оказывающих услугу."""
        await self.session.execute(
            delete(resource_services).where(
                resource_services.c.service_id == service_id
            )
        )
        unique_ids = list(dict.fromkeys(resource_ids))
        if unique_ids:
            await self.session.execute(
                insert(resource_services),
                [
                    {"resource_id": resource_id, "service_id": service_id}
                    for resource_id in unique_ids
                ],
            )

    async def get_resource_ids(self, service_id: int) -> set[int]:
        rows = await self.session.execute(
            select(resource_services.c.resource_id).where(
                resource_services.c.service_id == service_id
            )
        )
        return set(rows.scalars().all())
