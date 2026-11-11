from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Interval, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .book import Book
    from .breed import Breed
    from .service_consumable import ServiceConsumable
    from .book_service import BookService


class Service(Base):
    __tablename__ = "service"

    service_id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration: Mapped[timedelta | None] = mapped_column(Interval)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    breed_id: Mapped[int | None] = mapped_column(
        "breed",
        ForeignKey("breed.breed_id")
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
    book_services: Mapped[list["BookService"]] = relationship(
        "BookService",
        back_populates="service",
        lazy="selectin",
    )
