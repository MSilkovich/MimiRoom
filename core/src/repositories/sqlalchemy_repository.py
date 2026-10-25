from typing import Type, TypeVar, Optional, Generic

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.excpetions.crud import NotFoundError, ValidationError

from ..context import get_current_user
from ..models.base_model import Base

from .base import AbstractRepository


ModelType = TypeVar("ModelType", bound=Base)


class SqlAlchemyRepository(AbstractRepository, Generic[ModelType]):
    """Работает в переданной сессии (общий DbContext из UoW).

    Не открывает свою сессию и не коммитит — коммит/rollback выполняет UoW,
    чтобы несколько репозиториев работали в рамках одной транзакции.

    Поля аудита (who_create / who_update) заполняются автоматически из
    контекста текущего пользователя (см. src/context.py), который выставляется
    на уровне midleware. Так репозиторий знает, от чьего имени идёт изменение.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    @property
    def pk_name(self) -> str:
        return self.model.__mapper__.primary_key[0].name

    async def create(self, data: dict) -> ModelType:
        user = get_current_user()
        instance = self.model(**data)
        if hasattr(instance, "who_create"):
            instance.who_create = user.user_id
            instance.who_update = user.user_id
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, data: dict, **filters) -> ModelType:
        if not data:
            raise ValidationError("Нет данных для обновления")
        filters["is_deleted"] = False
        values = dict(data)
        user = get_current_user()
        if hasattr(self.model, "who_update"):
            values["who_update"] = user.user_id
        stmt = (
            update(self.model)
            .filter_by(**filters)
            .values(**values)
            .returning(self.model)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        if (ret := res.scalar_one_or_none()) is not None:
            return ret
        raise NotFoundError("Нечего изменять/удалять")

    async def delete_permanent(self, **filters) -> None:
        """Полное удаление записи из бд."""
        await self.session.execute(delete(self.model).filter_by(**filters))

    async def delete(self, **filters) -> None:
        """Удаление по умолчанию = soft delete, через пометку self.is_deleted=True"""
        await self.update({"is_deleted": True}, **filters)

    async def get_single(self, **filters) -> Optional[ModelType] | None:
        filters["is_deleted"] = False
        row = await self.session.execute(select(self.model).filter_by(**filters))
        return row.scalar_one_or_none()

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        **filters
    ) -> list[ModelType]:
        filters["is_deleted"] = False
        order_column = getattr(self.model, order) if order else getattr(
            self.model, self.pk_name)
        stmt = select(self.model).filter_by(**filters).order_by(
            order_column).limit(limit).offset(offset)
        row = await self.session.execute(stmt)
        return list(row.scalars().all())
