from datetime import datetime

from sqlalchemy import select, text

from ..models.booking import Booking
from ..models.enums.booking_status import BookingStatus
from ..models.slot import Slot
from .sqlalchemy_repository import SqlAlchemyRepository

# Пространство имён advisory-lock, чтобы не пересекаться с другими блокировками.
MASTER_LOCK_NAMESPACE = 74261


class BookingRepository(SqlAlchemyRepository[Booking]):
    def __init__(self, session):
        super().__init__(Booking, session)

    async def acquire_master_lock(self, master_id: int) -> None:
        """Транзакционный advisory-lock по мастеру.

        Сериализует создание/отмену броней одного мастера, поэтому два
        параллельных запроса на пересекающиеся слоты не пройдут одновременно.
        На не-PostgreSQL диалектах (например, в юнит-тестах) просто no-op:
        там защиту обеспечивает уникальный индекс по ``slot_id``.
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

        Связанные ``slot``, ``service``, ``client`` и ``pet`` подгружаются
        selectin'ом, чтобы в сервисном слое можно было посчитать интервал с
        учётом буферов без дополнительных запросов.
        """
        stmt = select(Booking).where(
            Booking.master_id == master_id,
            Booking.is_deleted.is_(False),
            Booking.status.in_(
                [BookingStatus.PENDING, BookingStatus.CONFIRMED]
            ),
        )
        if start is not None or end is not None:
            stmt = stmt.join(Slot, Booking.slot_id == Slot.slot_id)
            if start is not None:
                stmt = stmt.where(Slot.start_time >= start)
            if end is not None:
                stmt = stmt.where(Slot.start_time < end)
        stmt = stmt.order_by(Booking.booking_id)
        rows = await self.session.execute(stmt)
        return list(rows.scalars().unique().all())
