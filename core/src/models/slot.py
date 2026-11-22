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
    from .resource import Resource
    from .service import Service


class Slot(Base):
    """Слот — конкретный интервал времени мастера под конкретную услугу.

    Слоты генерируются по ``work_schedules`` и длительности услуги (+ буферы)
    модулем ``src/services/slot_generator.py``. ``start_time``/``end_time`` —
    это интервал самой услуги; буферы до/после учитываются при проверке
    пересечений (см. ``slot_generator.slot_footprint``).
    """

    __tablename__ = "slots"

    slot_id: Mapped[int] = mapped_column(primary_key=True)
    resource_id: Mapped[int] = mapped_column(
        ForeignKey("resources.resource_id", ondelete="CASCADE"),
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
        server_default=SlotStatus.FREE,
        nullable=False,
        index=True,
    )

    resource: Mapped["Resource"] = relationship(
        "Resource", back_populates="slots", lazy="selectin"
    )
    service: Mapped["Service"] = relationship("Service", lazy="selectin")
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking", back_populates="slot", lazy="selectin"
    )

    __table_args__ = (
        UniqueConstraint(
            "resource_id",
            "service_id",
            "start_time",
            name="uq_slots_resource_service_start",
        ),
        Index("ix_slots_resource_start", "resource_id", "start_time"),
    )
