from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .measure_unit import MeasureUnit
    from .service_consumable import ServiceConsumable


class Storage(Base):
    __tablename__ = "storage"

    item_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(255))
    measure_unit_id: Mapped[int | None] = mapped_column(
        "measure_unit",
        ForeignKey("measure_unit.measure_unit_id")
    )
    count: Mapped[int | None] = mapped_column(nullable=True)

    measure_unit: Mapped["MeasureUnit | None"] = relationship(
        "MeasureUnit",
        back_populates="storages",
        lazy="selectin"
    )
    consumables: Mapped[list["ServiceConsumable"]] = relationship(
        "ServiceConsumable",
        back_populates="consumable",
        lazy="selectin"
    )
