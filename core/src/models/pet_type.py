from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .breed import Breed


class PetType(Base):
    __tablename__ = "pet_type"

    pet_type_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(60), nullable=False)

    breeds: Mapped[list["Breed"]] = relationship(
        "Breed",
        back_populates="pet_type",
        lazy="selectin"
    )
