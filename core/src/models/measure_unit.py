from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .storage import Storage


class MeasureUnit(Base):
    __tablename__ = "measure_unit"

    measure_unit_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(60))

    storages: Mapped[list["Storage"]] = relationship(
        "Storage",
        back_populates="measure_unit",
        lazy="selectin"
    )
