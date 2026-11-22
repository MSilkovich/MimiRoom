from src.excpetions.crud import ValidationError
from src.models.service import Service
from src.models.service_consumable import ServiceConsumable
from src.models.resource import Resource
from ..schemas import ServiceCreate, ServiceUpdate
from .base import BaseService


class ServiceService(BaseService[Service, ServiceCreate, ServiceUpdate]):
    model = Service

    @staticmethod
    async def _ensure_resources_exist(
        resource_repo, resource_ids: list[int]
    ) -> None:
        unique_ids = set(resource_ids)
        found = await resource_repo.get_many_by_ids(unique_ids)
        missing = unique_ids - {resource.resource_id for resource in found}
        if missing:
            raise ValidationError(f"Мастера не найдены: {sorted(missing)}")

    async def create(self, data: ServiceCreate) -> Service:
        async with self.uow_factory() as uow:
            service_repo = uow.repository(Service)
            consumable_repo = uow.repository(ServiceConsumable)
            resource_repo = uow.repository(Resource)

            payload = data.model_dump(exclude={"consumables", "resource_ids"})
            service = await service_repo.create(payload)
            service_id = service.service_id

            if data.resource_ids:
                await self._ensure_resources_exist(
                    resource_repo, data.resource_ids
                )
                await service_repo.replace_resources(
                    service_id, data.resource_ids
                )

            if data.consumables:
                await consumable_repo.create_many([
                    {**c.model_dump(), "service_id": service_id}
                    for c in data.consumables
                ])

            await uow.commit()
            uow.session.expire_all()
            reloaded = await service_repo.get_single(service_id=service_id)
            return reloaded or service

    async def update(
        self, pk: int, data: ServiceUpdate
    ) -> Service | None:
        async with self.uow_factory() as uow:
            service_repo = uow.repository(Service)
            resource_repo = uow.repository(Resource)

            payload = data.model_dump(
                exclude_unset=True, exclude={"resource_ids"}
            )
            if payload:
                service = await service_repo.update(
                    payload, service_id=pk
                )
            else:
                service = await service_repo.get_single(service_id=pk)
            if service is None:
                return None

            if data.resource_ids is not None:
                await self._ensure_resources_exist(
                    resource_repo, data.resource_ids
                )
                await service_repo.replace_resources(pk, data.resource_ids)

            await uow.commit()
            uow.session.expire_all()
            return await service_repo.get_single(service_id=pk)
