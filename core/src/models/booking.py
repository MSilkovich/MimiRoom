from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Enum as SAEnum,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base
from .enums.booking_status import BookingStatus

if TYPE_CHECKING:
    from .pet import Pet
    from .service import Service
    from .slot import Slot
    from .user import User


class Booking(Base):
    """Бронирование слота.

    Мастер — ``master_id`` (FK ``user`` с ролью ``groomer``). Клиент может
    быть авторизованным (``client_id``) либо гостем (контакт в
    ``client_name``/``client_phone``). Питомец — ``pet_id``. ``options`` —
    произвольные доп. данные (в т.ч. сырой payload интеграции).

    Защита от двойного бронирования:
    - частичный уникальный индекс ``uq_bookings_active_slot`` по ``slot_id``
      для всех статусов, кроме ``cancelled``;
    - дополнительно сервисный слой берёт advisory-lock по мастеру и
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
    master_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # участники
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.user_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    pet_id: Mapped[int | None] = mapped_column(
        ForeignKey("pet.pet_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # контакт-снимок / данные гостя (nullable, если есть client_id)
    client_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    client_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    status: Mapped[BookingStatus] = mapped_column(
        SAEnum(BookingStatus, name="booking_status"),
        default=BookingStatus.PENDING,
        server_default=BookingStatus.PENDING.name,
        nullable=False,
        index=True,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    slot: Mapped["Slot"] = relationship(
        "Slot", back_populates="bookings", lazy="selectin"
    )
    service: Mapped["Service"] = relationship("Service", lazy="selectin")
    master: Mapped["User"] = relationship(
        "User",
        back_populates="bookings_as_master",
        foreign_keys=[master_id],
        lazy="selectin",
    )
    client: Mapped["User | None"] = relationship(
        "User",
        back_populates="bookings_as_client",
        foreign_keys=[client_id],
        lazy="selectin",
    )
    pet: Mapped["Pet | None"] = relationship(
        "Pet", back_populates="bookings", lazy="selectin"
    )

    __table_args__ = (
        # один слот — не более одного активного (не отменённого) бронирования
        Index(
            "uq_bookings_active_slot",
            "slot_id",
            unique=True,
            postgresql_where=text("status <> 'CANCELLED'"),
        ),
        Index("ix_bookings_master_status", "master_id", "status"),
    )
