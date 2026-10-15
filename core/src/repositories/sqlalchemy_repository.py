from typing import Type, TypeVar, Optional, Generic

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.base_model import Base
from ..context import get_current_user_id

from .base_repository import AbstractRepository


ModelType = TypeVar("ModelType", bound=Base)


class SqlAlchemyRepository(AbstractRepository, Generic[ModelType]):
    """Работает в переданной сессии (общий DbContext из UoW).

    Не открывает свою сессию и не коммитит — коммит/rollback выполняет UoW,
    чтобы несколько репозиториев работали в рамках одной транзакции.

    Поля аудита (who_create / who_update) заполняются автоматически из
    контекста текущего пользователя (см. src/context.py), который выставляется
    на уровне роутера. Так репозиторий знает, от чьего имени идёт изменение.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    @property
    def pk_name(self) -> str:
        return self.model.__mapper__.primary_key[0].name

    async def create(self, data: dict) -> ModelType:
        user_id = get_current_user_id()
        instance = self.model(**data)
        if hasattr(instance, "who_create"):
            instance.who_create = user_id
            instance.who_update = user_id
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, data: dict, **filters) -> ModelType:
        if not data:
            raise ValueError("update: нет данных для обновления")
        if not filters:
            filters = {self.pk_name: data[self.pk_name]}
        values = dict(data)
        user_id = get_current_user_id()
        # who_update фиксируем только когда пользователь известен, иначе
        # затирали бы прежнее значение NULL-ом.
        if user_id is not None and hasattr(self.model, "who_update"):
            values["who_update"] = user_id
        stmt = (
            update(self.model)
            .filter_by(**filters)
            .values(**values)
            .returning(self.model)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        return res.scalar_one()

    async def delete(self, **filters) -> None:
        await self.session.execute(delete(self.model).filter_by(**filters))
        await self.session.flush()

    async def get_single(self, **filters) -> Optional[ModelType] | None:
        row = await self.session.execute(select(self.model).filter_by(**filters))
        return row.scalar_one_or_none()

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ModelType]:
        order_column = getattr(self.model, order) if order else getattr(self.model, self.pk_name)
        stmt = select(self.model).order_by(order_column).limit(limit).offset(offset)
        row = await self.session.execute(stmt)
        return list(row.scalars().all())

