from datetime import timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Interval, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .book import Book
    from .service import Service
    from .user import User


class BookService(Base):
    __tablename__ = "book_service"

    id: Mapped[int] = mapped_column(primary_key=True)

    book_id: Mapped[int] = mapped_column(
        ForeignKey("book.book_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[int] = mapped_column(
        ForeignKey("service.service_id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    master_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.user_id", ondelete="RESTRICT"),
        nullable=True,
    )

    # снапшот на момент брони
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    price_at_booking: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False)

    book: Mapped["Book"] = relationship("Book", back_populates="services")
    service: Mapped["Service"] = relationship(
        "Service", back_populates="book_services", lazy="selectin")
    master: Mapped["User | None"] = relationship("User", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("book_id", "service_id",
                         "master_id", name="uq_book_service"),
    )
