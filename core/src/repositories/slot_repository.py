from datetime import datetime
from typing import Iterable

from sqlalchemy import select

from ..context import get_current_user
from ..models.slot import Slot
from .sqlalchemy_repository import SqlAlchemyRepository


class SlotRepository(SqlAlchemyRepository[Slot]):
    def __init__(self, session):
        super().__init__(Slot, session)

    async def get_for_update(self, slot_id: int) -> Slot | None:
        """Прочитать слот с блокировкой строки (``SELECT ... FOR UPDATE``)."""
        stmt = (
            select(Slot)
            .where(Slot.slot_id == slot_id, Slot.is_deleted.is_(False))
            .with_for_update()
        )
        row = await self.session.execute(stmt)
        return row.scalar_one_or_none()

    async def list_range(
        self,
        resource_id: int,
        start: datetime,
        end: datetime,
        service_id: int | None = None,
    ) -> list[Slot]:
        """Слоты мастера, начинающиеся в интервале ``[start, end)``."""
        stmt = select(Slot).where(
            Slot.resource_id == resource_id,
            Slot.start_time >= start,
            Slot.start_time < end,
            Slot.is_deleted.is_(False),
        )
        if service_id is not None:
            stmt = stmt.where(Slot.service_id == service_id)
        stmt = stmt.order_by(Slot.start_time, Slot.service_id)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def existing_start_times(
        self,
        resource_id: int,
        service_id: int,
        start: datetime,
        end: datetime,
    ) -> set[datetime]:
        """Уже существующие ``start_time`` (для идемпотентной генерации)."""
        stmt = select(Slot.start_time).where(
            Slot.resource_id == resource_id,
            Slot.service_id == service_id,
            Slot.start_time >= start,
            Slot.start_time < end,
            Slot.is_deleted.is_(False),
        )
        rows = await self.session.execute(stmt)
        return set(rows.scalars().all())

    async def list_filtered(
        self,
        resource_id: int | None = None,
        service_id: int | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        status=None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Slot]:
        stmt = select(Slot).where(Slot.is_deleted.is_(False))
        if resource_id is not None:
            stmt = stmt.where(Slot.resource_id == resource_id)
        if service_id is not None:
            stmt = stmt.where(Slot.service_id == service_id)
        if start is not None:
            stmt = stmt.where(Slot.start_time >= start)
        if end is not None:
            stmt = stmt.where(Slot.start_time < end)
        if status is not None:
            stmt = stmt.where(Slot.status == status)
        stmt = stmt.order_by(Slot.start_time, Slot.slot_id).limit(limit).offset(offset)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().all())

    async def create_many(self, items: Iterable[dict]) -> list[Slot]:
        """Пакетная вставка слотов.

        Слоты генерируются системой, поэтому при отсутствии пользовательского
        контекста поля аудита заполняются «системным» id (0), чтобы не нарушать
        NOT NULL на ``who_create``/``who_update``.
        """
        user = get_current_user()
        user_id = user.user_id if user is not None else 0

        instances: list[Slot] = []
        for data in items:
            instance = self.model(**data)
            instance.who_create = user_id
            instance.who_update = user_id
            self.session.add(instance)
            instances.append(instance)

        await self.session.flush()
        return instances
