from datetime import date as date_type, time as time_type
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .pet import Pet
    from .service import Service
    from .user import User


class Book(Base):
    __tablename__ = "book"

    book_id: Mapped[int] = mapped_column(primary_key=True)
    pet_id: Mapped[int | None] = mapped_column(
        "pet",
        ForeignKey("pet.pet_id")
    )
    master_id: Mapped[int | None] = mapped_column(
        "master",
        ForeignKey("user.user_id")
    )
    date: Mapped[date_type | None] = mapped_column(Date)
    time: Mapped[time_type | None] = mapped_column(Time)
    service_id: Mapped[int | None] = mapped_column(
        "service",
        ForeignKey("service.service_id")
    )

    pet: Mapped["Pet | None"] = relationship(
        "Pet",
        back_populates="books",
        lazy="selectin"
    )
    master: Mapped["User | None"] = relationship(
        "User",
        back_populates="books",
        lazy="selectin"
    )
    service: Mapped["Service | None"] = relationship(
        "Service",
        back_populates="books",
        lazy="selectin"
    )
