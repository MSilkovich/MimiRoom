from sqlalchemy import delete, insert, select

from ..models.resource import Resource, resource_services
from .sqlalchemy_repository import SqlAlchemyRepository


class ResourceRepository(SqlAlchemyRepository[Resource]):
    def __init__(self, session):
        super().__init__(Resource, session)

    async def replace_services(
        self, resource_id: int, service_ids: list[int]
    ) -> None:
        """Полностью переписать набор услуг мастера (many-to-many)."""
        await self.session.execute(
            delete(resource_services).where(
                resource_services.c.resource_id == resource_id
            )
        )
        unique_ids = list(dict.fromkeys(service_ids))
        if unique_ids:
            await self.session.execute(
                insert(resource_services),
                [
                    {"resource_id": resource_id, "service_id": service_id}
                    for service_id in unique_ids
                ],
            )

    async def get_service_ids(self, resource_id: int) -> set[int]:
        rows = await self.session.execute(
            select(resource_services.c.service_id).where(
                resource_services.c.resource_id == resource_id
            )
        )
        return set(rows.scalars().all())
