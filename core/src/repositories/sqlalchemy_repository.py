from typing import Type, TypeVar, Optional, Generic

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.excpetions.crud import NotFoundError, ValidationError
from src.permissions.enums.scope import Scope
from src.permissions.permission_rule import PermissionRule

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

    Методы получают сверху опциональные правила доступа, реализуйте проверки здесь
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    @property
    def pk_name(self) -> str:
        return self.model.__mapper__.primary_key[0].name

    def _owner_field(self, rule: PermissionRule | None) -> str | None:
        """Колонка, по которой ограничивается OWN-доступ для модели."""
        if rule is None or rule.scope != Scope.OWN:
            return None
        field = rule.owner_field or "who_create"
        # Используем имя mapped-атрибута, а не имя колонки в БД: у части моделей
        # они различаются (например, Pet.owner_id -> колонка ``owner``).
        if hasattr(self.model, field):
            return field
        if hasattr(self.model, "who_create"):
            return "who_create"
        return None

    async def create(self, data: dict, rule: PermissionRule | None = None) -> ModelType:
        # не обязательно проверять, это уже долно стрельнуть в ручке
        user = get_current_user()
        payload = dict(data)
        owner_field = self._owner_field(rule)
        if owner_field is not None and owner_field != "who_create":
            # OWN-создание: владелец всегда текущий пользователь.
            payload[owner_field] = rule.owner_id
        instance = self.model(**payload)
        if hasattr(instance, "who_create"):
            instance.who_create = user.user_id
            instance.who_update = user.user_id
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, data: dict, rule: PermissionRule | None = None, **filters) -> ModelType:
        owner_field = self._owner_field(rule)
        if not data:
            raise ValidationError("Нет данных для обновления")
        filters["is_deleted"] = False
        values = dict(data)
        # Не позволяем OWN-пользователю «переписать» владельца и выпасть из области.
        if owner_field is not None and owner_field != "who_create":
            values.pop(owner_field, None)
        user = get_current_user()
        if hasattr(self.model, "who_update"):
            values["who_update"] = user.user_id

        # Owner-ограничение добавляем отдельным WHERE, а не в filters:
        # иначе для моделей, где owner_field совпадает с PK (User.user_id),
        # оно перезапишет целевой pk и обновит профиль текущего пользователя.
        stmt = update(self.model)
        if owner_field is not None:
            stmt = stmt.where(
                rule.sql_filter(getattr(self.model, owner_field))
            )
        stmt = (
            stmt
            .filter_by(**filters)
            .values(**values)
            .returning(self.model)
        )
        res = await self.session.execute(stmt)
        await self.session.flush()
        if (ret := res.scalar_one_or_none()) is not None:
            return ret
        raise NotFoundError("Нечего изменять/удалять")

    async def delete_permanent(self, rule: PermissionRule | None = None, **filters) -> None:
        """Полное удаление записи из бд."""
        owner_field = self._owner_field(rule)
        stmt = delete(self.model)
        if owner_field is not None:
            stmt = stmt.where(
                rule.sql_filter(getattr(self.model, owner_field))
            )
        if filters:
            stmt = stmt.filter_by(**filters)
        await self.session.execute(stmt)

    async def delete(self, rule: PermissionRule | None = None, **filters) -> None:
        """Удаление по умолчанию = soft delete, через пометку self.is_deleted=True"""
        await self.update({"is_deleted": True}, rule=rule, **filters)

    async def get_single(self, rule: PermissionRule | None = None, **filters) -> Optional[ModelType] | None:
        filters["is_deleted"] = False
        smth = select(self.model)
        owner_field = self._owner_field(rule)
        if owner_field is not None:
            smth = smth.where(rule.sql_filter(
                getattr(self.model, owner_field)))
        smth = smth.filter_by(**filters)
        row = await self.session.execute(smth)
        return row.scalar_one_or_none()

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        rule: PermissionRule | None = None,
        **filters
    ) -> list[ModelType]:
        filters["is_deleted"] = False
        order_column = getattr(self.model, order) if order else getattr(
            self.model, self.pk_name)
        smth = select(self.model)
        owner_field = self._owner_field(rule)
        if owner_field is not None:
            smth = smth.where(rule.sql_filter(
                getattr(self.model, owner_field)))
        smth = smth.filter_by(**filters).order_by(
            order_column).limit(limit).offset(offset)
        row = await self.session.execute(smth)
        return list(row.scalars().all())

    async def get_many_by_ids(
        self,
        ids: set[int],
        rule: PermissionRule | None = None,
        include_deleted: bool = False,
    ) -> list[ModelType]:
        if not ids:
            return []
        pk = getattr(self.model, self.pk_name)
        smth = select(self.model).where(pk.in_(ids))
        if not include_deleted and hasattr(self.model, "is_deleted"):
            smth = smth.where(self.model.is_deleted.is_(False))
        owner_field = self._owner_field(rule)
        if owner_field is not None:
            smth = smth.where(rule.sql_filter(
                getattr(self.model, owner_field)))
        row = await self.session.execute(smth)
        return list(row.scalars().all())
