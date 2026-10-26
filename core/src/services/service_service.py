from src.models.service_consumable import ServiceConsumable
from ..models.service import Service
from ..schemas import ServiceCreate, ServiceUpdate
from .base_service import BaseService


class ServiceService(BaseService[Service, ServiceCreate, ServiceUpdate]):
    model = Service

    async def create(self, data: ServiceCreate) -> Service:
        async with self.uow_factory() as uow:
            service_repo = uow.repository(Service)
            consumable_repo = uow.repository(ServiceConsumable)

            payload = data.model_dump(exclude={"consumables"})
            service = await service_repo.create(payload)

            if data.consumables:
                await consumable_repo.create_many([
                    {**c.model_dump(), "service_id": service.service_id}
                    for c in data.consumables
                ])

            await uow.commit()
            return service
