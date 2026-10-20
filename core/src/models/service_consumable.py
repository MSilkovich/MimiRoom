from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .service import Service
    from .storage import Storage


class ServiceConsumable(Base):
    __tablename__ = "service_consumables"

    service_id: Mapped[int] = mapped_column(
        "service",
        ForeignKey("service.service_id"),
        primary_key=True
    )
    consumable_id: Mapped[int] = mapped_column(
        "consumable",
        ForeignKey("storage.item_id"),
        primary_key=True
    )
    volume: Mapped[int | None] = mapped_column(nullable=True)

    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="consumables",
        lazy="selectin"
    )
    consumable: Mapped["Storage"] = relationship(
        "Storage",
        back_populates="consumables",
        lazy="selectin"
    )
