from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Interval, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .breed import Breed
    from .service_consumable import ServiceConsumable
    from .user import User


class Service(Base):
    __tablename__ = "service"

    service_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[timedelta | None] = mapped_column(Interval)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # Буферы вокруг услуги: время на подготовку/уборку. Участвуют в расчёте
    # сетки слотов и проверке пересечений, но не «продаются» клиенту.
    buffer_before_minutes: Mapped[int] = mapped_column(
        nullable=False, default=0, server_default="0"
    )
    buffer_after_minutes: Mapped[int] = mapped_column(
        nullable=False, default=0, server_default="0"
    )
    breed_id: Mapped[int | None] = mapped_column(
        "breed",
        ForeignKey("breed.breed_id")
    )

    @property
    def duration_minutes(self) -> int | None:
        """Длительность услуги в минутах (``None``, если не задана)."""
        if self.duration is None:
            return None
        return int(self.duration.total_seconds() // 60)

    masters: Mapped[list["User"]] = relationship(
        "User",
        secondary="master_services",
        lazy="selectin",
        viewonly=True,
    )

    breed: Mapped["Breed | None"] = relationship(
        "Breed",
        back_populates="services",
        lazy="selectin"
    )
    consumables: Mapped[list["ServiceConsumable"]] = relationship(
        "ServiceConsumable",
        back_populates="service",
        lazy="selectin"
    )
