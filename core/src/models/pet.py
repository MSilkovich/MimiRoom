from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .breed import Breed
    from .book import Book
    from .user import User


class Pet(Base):
    __tablename__ = "pet"

    pet_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    owner_id: Mapped[int | None] = mapped_column(
        "owner",
        ForeignKey("user.user_id")
    )
    birthday: Mapped[date | None] = mapped_column(Date)
    breed_id: Mapped[int | None] = mapped_column(
        "breed",
        ForeignKey("breed.breed_id")
    )

    owner: Mapped["User | None"] = relationship(
        "User",
        back_populates="pets",
        lazy="selectin"
    )
    breed: Mapped["Breed | None"] = relationship(
        "Breed",
        back_populates="pets",
        lazy="selectin"
    )
    books: Mapped[list["Book"]] = relationship(
        "Book",
        back_populates="pet",
        lazy="selectin"
    )
