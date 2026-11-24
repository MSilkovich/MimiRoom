from datetime import datetime

from sqlalchemy import select, text

from ..models.booking import Booking
from ..models.enums.booking_status import BookingStatus
from ..permissions.enums.scope import Scope
from .sqlalchemy_repository import SqlAlchemyRepository

# Пространство имён advisory-lock, чтобы не пересекаться с другими блокировками.
MASTER_LOCK_NAMESPACE = 74261


class BookingRepository(SqlAlchemyRepository[Booking]):
    def __init__(self, session):
        super().__init__(Booking, session)

    async def acquire_master_lock(self, master_id: int) -> None:
        """Транзакционный advisory-lock по мастеру.

        Сериализует создание/отмену броней одного мастера, поэтому два
        параллельных запроса на пересекающиеся интервалы не пройдут
        одновременно: второй увидит уже зафиксированную первую бронь и
        получит конфликт по пересечению. На не-PostgreSQL диалектах
        (например, в юнит-тестах) это no-op.
        """
        bind = self.session.get_bind()
        if bind.dialect.name != "postgresql":
            return
        await self.session.execute(
            text("SELECT pg_advisory_xact_lock(:namespace, :key)"),
            {"namespace": MASTER_LOCK_NAMESPACE, "key": master_id},
        )

    async def get_active_for_master(
        self,
        master_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[Booking]:
        """Активные (не отменённые) брони мастера; при желании — в окне дат.

        Связанные ``service``, ``client`` и ``pet`` подгружаются selectin'ом,
        чтобы в сервисном слое можно было посчитать footprint с учётом буферов
        услуги без дополнительных запросов.
        """
        stmt = select(Booking).where(
            Booking.master_id == master_id,
            Booking.is_deleted.is_(False),
            Booking.status.in_(
                [
                    BookingStatus.PENDING,
                    BookingStatus.CONFIRMED,
                    BookingStatus.COMPLETED,
                ]
            ),
        )
        if start is not None:
            stmt = stmt.where(Booking.start_time >= start)
        if end is not None:
            stmt = stmt.where(Booking.start_time < end)
        stmt = stmt.order_by(Booking.booking_id)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().unique().all())

    async def get_multi_by_period(
        self,
        start_from: datetime | None = None,
        start_to: datetime | None = None,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        rule=None,
        **filters,
    ) -> list[Booking]:
        """Список броней с фильтром по диапазону ``start_time``.

        ``start_from`` — включительно, ``start_to`` — исключительно
        (границы уже приведены к таймзоне на уровне сервиса).
        """
        filters["is_deleted"] = False
        stmt = select(Booking)
        if rule is not None and rule.scope == Scope.OWN:
            stmt = stmt.where(rule.sql_filter(Booking.who_create))
        if filters:
            stmt = stmt.filter_by(**filters)
        if start_from is not None:
            stmt = stmt.where(Booking.start_time >= start_from)
        if start_to is not None:
            stmt = stmt.where(Booking.start_time < start_to)
        order_column = (
            getattr(self.model, order)
            if order
            else getattr(self.model, self.pk_name)
        )
        stmt = stmt.order_by(order_column).limit(limit).offset(offset)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().unique().all())

    async def get_for_pet(
        self,
        pet_id: int,
        status: BookingStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Booking]:
        """История посещений питомца (все брони, новые сверху)."""
        stmt = select(Booking).where(
            Booking.pet_id == pet_id,
            Booking.is_deleted.is_(False),
        )
        if status is not None:
            stmt = stmt.where(Booking.status == status)
        stmt = stmt.order_by(Booking.start_time.desc()).limit(limit).offset(offset)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().unique().all())
