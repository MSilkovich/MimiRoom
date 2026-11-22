from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base
from .enums.slot_status import SlotStatus

if TYPE_CHECKING:
    from .booking import Booking
    from .service import Service
    from .user import User


class Slot(Base):
    """Слот — конкретный интервал времени мастера под конкретную услугу.

    Мастер — это ``user`` (``master_id``). Слоты генерируются по
    ``work_schedules`` и длительности услуги (+ буферы) модулем
    ``src/services/slot_generator.py``. ``start_time``/``end_time`` — интервал
    самой услуги; буферы до/после учитываются при проверке пересечений.
    """

    __tablename__ = "slots"

    slot_id: Mapped[int] = mapped_column(primary_key=True)
    master_id: Mapped[int] = mapped_column(
        ForeignKey("user.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service.service_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    start_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[SlotStatus] = mapped_column(
        SAEnum(SlotStatus, name="slot_status"),
        default=SlotStatus.FREE,
        server_default=SlotStatus.FREE.name,
        nullable=False,
        index=True,
    )

    master: Mapped["User"] = relationship(
        "User", back_populates="slots", lazy="selectin"
    )
    service: Mapped["Service"] = relationship("Service", lazy="selectin")
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="slot", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "master_id",
            "service_id",
            "start_time",
            name="uq_slots_master_service_start",
        ),
        Index("ix_slots_master_start", "master_id", "start_time"),
    )
