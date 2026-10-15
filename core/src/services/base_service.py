from typing import Optional

from .generic_service import (
    GenericService,
    ModelType,
    CreateSchemaType,
    UpdateSchemaType,
)


class BaseService(GenericService[ModelType, CreateSchemaType, UpdateSchemaType]):
    """CRUD поверх Unit of Work.

    Каждая операция открывает свой UoW (свою транзакцию), получает нужный
    репозиторий по классу модели и фиксирует изменения через ``uow.commit()``.
    Первичный ключ берётся из репозитория (доменный, например ``user_id``).
    """

    async def create(self, data: CreateSchemaType) -> ModelType:
        async with self.uow_factory() as uow:
            repo = uow.repository(self.model)
            instance = await repo.create(data.model_dump())
            await uow.commit()
            return instance

    async def update(self, pk: int, data: UpdateSchemaType) -> ModelType:
        async with self.uow_factory() as uow:
            repo = uow.repository(self.model)
            instance = await repo.update(
                data.model_dump(exclude_unset=True),
                **{repo.pk_name: pk},
            )
            await uow.commit()
            return instance

    async def get(self, pk: int) -> Optional[ModelType] | None:
        async with self.uow_factory() as uow:
            repo = uow.repository(self.model)
            return await repo.get_single(**{repo.pk_name: pk})

    async def delete(self, pk: int) -> None:
        async with self.uow_factory() as uow:
            repo = uow.repository(self.model)
            await repo.delete(**{repo.pk_name: pk})
            await uow.commit()

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        async with self.uow_factory() as uow:
            repo = uow.repository(self.model)
            return await repo.get_multi(order=order, limit=limit, offset=offset)

