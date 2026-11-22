from typing import TYPE_CHECKING

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base
from .enums.booking_status import BookingStatus

if TYPE_CHECKING:
    from .resource import Resource
    from .service import Service
    from .slot import Slot


class Booking(Base):
    """Бронирование слота.

    Заменяет ``book`` как основную таблицу новых записей. Старая ``book``
    остаётся доступной только для чтения (legacy).

    Защита от двойного бронирования:
    - частичный уникальный индекс ``uq_bookings_active_slot`` по ``slot_id``
      для всех статусов, кроме ``cancelled``;
    - дополнительно сервисный слой берёт advisory-lock по ресурсу и
      ``SELECT ... FOR UPDATE`` по строке слота (см. ``BookingService.create``).
    """

    __tablename__ = "bookings"

    booking_id: Mapped[int] = mapped_column(primary_key=True)
    slot_id: Mapped[int] = mapped_column(
        ForeignKey("slots.slot_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service.service_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.resource_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    client_name: Mapped[str] = mapped_column(String(255), nullable=False)
    client_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        server_default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    slot: Mapped["Slot"] = relationship(
        "Slot", back_populates="bookings", lazy="selectin"
    )
    service: Mapped["Service"] = relationship("Service", lazy="selectin")
    resource: Mapped["Resource"] = relationship(
        "Resource", back_populates="bookings", lazy="selectin"
    )

    __table_args__ = (
        # один слот — не более одного активного (не отменённого) бронирования
        Index(
            "uq_bookings_active_slot",
            "slot_id",
            unique=True,
            postgresql_where=text("status <> 'CANCELLED'"),
        ),
        Index("ix_bookings_resource_status", "resource_id", "status"),
    )
