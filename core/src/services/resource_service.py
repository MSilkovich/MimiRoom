from src.excpetions.crud import ValidationError
from src.models.resource import Resource
from src.models.service import Service
from src.schemas import ResourceCreate, ResourceUpdate
from .base import BaseService


class ResourceService(BaseService[Resource, ResourceCreate, ResourceUpdate]):
    model = Resource

    @staticmethod
    async def _ensure_services_exist(service_repo, service_ids: list[int]) -> None:
        """Проверить, что все привязываемые услуги существуют."""
        unique_ids = set(service_ids)
        found = await service_repo.get_many_by_ids(unique_ids)
        missing = unique_ids - {service.service_id for service in found}
        if missing:
            raise ValidationError(f"Услуги не найдены: {sorted(missing)}")

    async def create(self, data: ResourceCreate) -> Resource:
        async with self.uow_factory() as uow:
            resource_repo = uow.repository(Resource)
            service_repo = uow.repository(Service)

            payload = data.model_dump(exclude={"service_ids"})
            resource = await resource_repo.create(payload)
            resource_id = resource.resource_id

            if data.service_ids:
                await self._ensure_services_exist(service_repo, data.service_ids)
                await resource_repo.replace_services(
                    resource_id, data.service_ids
                )

            await uow.commit()
            uow.session.expire_all()
            reloaded = await resource_repo.get_single(
                resource_id=resource_id
            )
            return reloaded or resource

    async def update(
        self, pk: int, data: ResourceUpdate
    ) -> Resource | None:
        async with self.uow_factory() as uow:
            resource_repo = uow.repository(Resource)
            service_repo = uow.repository(Service)

            payload = data.model_dump(
                exclude_unset=True, exclude={"service_ids"}
            )
            resource = None
            if payload:
                resource = await resource_repo.update(
                    payload, resource_id=pk
                )
            else:
                resource = await resource_repo.get_single(resource_id=pk)

            if resource is None:
                return None

            if data.service_ids is not None:
                await self._ensure_services_exist(service_repo, data.service_ids)
                await resource_repo.replace_services(pk, data.service_ids)

            await uow.commit()
            uow.session.expire_all()
            return await resource_repo.get_single(resource_id=pk)
