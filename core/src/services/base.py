from typing import Optional

from src.permissions.permission_rule import PermissionRule
from src.repositories.sqlalchemy_repository import SqlAlchemyRepository

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

    Проксирует rule: PermissionRule | None = None на уровень репозиториев
    """

    async def create(self, data: CreateSchemaType, rule: PermissionRule | None = None) -> ModelType:
        async with self.uow_factory() as uow:
            repo: SqlAlchemyRepository = uow.repository(self.model)
            instance = await repo.create(data.model_dump(), rule)
            await uow.commit()
            return instance

    async def update(self, pk: int, data: UpdateSchemaType, rule: PermissionRule | None = None) -> ModelType:
        async with self.uow_factory() as uow:
            repo: SqlAlchemyRepository = uow.repository(self.model)
            instance = await repo.update(
                data.model_dump(exclude_unset=True),
                rule,
                **{repo.pk_name: pk},
            )
            await uow.commit()
            return instance

    async def get(self, pk: int, rule: PermissionRule | None = None) -> Optional[ModelType] | None:
        async with self.uow_factory() as uow:
            repo: SqlAlchemyRepository = uow.repository(self.model)
            return await repo.get_single(rule=rule, **{repo.pk_name: pk})

    async def delete(self, pk: int, rule: PermissionRule | None = None) -> None:
        async with self.uow_factory() as uow:
            repo: SqlAlchemyRepository = uow.repository(self.model)
            await repo.delete(rule=rule, **{repo.pk_name: pk})
            await uow.commit()

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        rule: PermissionRule | None = None,
    ) -> list[ModelType]:
        async with self.uow_factory() as uow:
            repo: SqlAlchemyRepository = uow.repository(self.model)
            return await repo.get_multi(order=order, limit=limit, offset=offset, rule=rule)
