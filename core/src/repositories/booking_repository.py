from datetime import datetime

from sqlalchemy import select, text

from ..models.booking import Booking
from ..models.enums.booking_status import BookingStatus
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
                [BookingStatus.PENDING, BookingStatus.CONFIRMED]
            ),
        )
        if start is not None:
            stmt = stmt.where(Booking.start_time >= start)
        if end is not None:
            stmt = stmt.where(Booking.start_time < end)
        stmt = stmt.order_by(Booking.booking_id)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().unique().all())
