from ..models.service_consumable import ServiceConsumable
from .sqlalchemy_repository import SqlAlchemyRepository
from ..context import get_current_user


class ServiceConsumableRepository(SqlAlchemyRepository[ServiceConsumable]):
    def __init__(self, session):
        super().__init__(ServiceConsumable, session)

    async def create_many(self, items: list[dict]) -> list[ServiceConsumable]:
        user = get_current_user()
        instances = []
        for data in items:
            inst = self.model(**data)
            if hasattr(inst, "who_create"):
                inst.who_create = user.user_id
                inst.who_update = user.user_id
            self.session.add(inst)
            instances.append(inst)
        await self.session.flush()
        return instances
