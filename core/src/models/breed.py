from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .pet import Pet
    from .pet_type import PetType
    from .service import Service


class Breed(Base):
    __tablename__ = "breed"

    breed_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(60))
    pet_type_id: Mapped[int | None] = mapped_column(
        "pet_type",
        ForeignKey("pet_type.pet_type_id")
    )

    pet_type: Mapped["PetType | None"] = relationship(
        "PetType",
        back_populates="breeds",
        lazy="selectin"
    )
    pets: Mapped[list["Pet"]] = relationship(
        "Pet",
        back_populates="breed",
        lazy="selectin"
    )
    services: Mapped[list["Service"]] = relationship(
        "Service",
        back_populates="breed",
        lazy="selectin"
    )
