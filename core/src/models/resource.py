from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    String,
    Table,
    Text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .booking import Booking
    from .service import Service
    from .slot import Slot
    from .work_schedule import WorkSchedule


# many-to-many: какие мастера (ресурсы) оказывают какие услуги.
# Ассоциативная таблица без собственных полей, поэтому оформлена как ``Table``.
resource_services = Table(
    "resource_services",
    Base.metadata,
    Column(
        "resource_id",
        ForeignKey("resources.resource_id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "service_id",
        ForeignKey("service.service_id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Resource(Base):
    """Мастер / исполнитель (в перспективе — любой бронируемый ресурс).

    На текущем этапе организация одна, поэтому ``organization_id`` заложен
    «на будущее» и может быть NULL.
    """

    __tablename__ = "resources"

    resource_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=true()
    )
    organization_id: Mapped[int | None] = mapped_column(nullable=True)

    services: Mapped[list["Service"]] = relationship(
        "Service",
        secondary=resource_services,
        back_populates="resources",
        lazy="selectin",
    )
    work_schedules: Mapped[list["WorkSchedule"]] = relationship(
        "WorkSchedule",
        back_populates="resource",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    slots: Mapped[list["Slot"]] = relationship(
        "Slot",
        back_populates="resource",
        lazy="selectin",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="resource",
        lazy="selectin",
    )
