from datetime import date as date_type, datetime, time as time_type
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    Date, DateTime, Enum as SAEnum, ForeignKey, Index,
    Text, Time,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .enums.book_source import BookSource
from .enums.book_status import BookStatus

from .base_model import Base

if TYPE_CHECKING:
    from .book_service import BookService
    from .pet import Pet
    from .user import User


class Book(Base):
    __tablename__ = "book"

    book_id: Mapped[int] = mapped_column(primary_key=True)

    status: Mapped[BookStatus] = mapped_column(
        SAEnum(BookStatus, name="book_status"),
        default=BookStatus.PENDING,
        server_default=BookStatus.PENDING,
        nullable=False,
        index=True,
    )
    source: Mapped[BookSource | None] = mapped_column(
        SAEnum(BookSource, name="book_source"),
        nullable=True,
    )

    # участники
    pet_id: Mapped[int | None] = mapped_column(
        ForeignKey("pet.pet_id"),
        nullable=True,
    )
    master_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.user_id"),
        nullable=True,
    )
    client_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.user_id"),
        nullable=True,
    )

    # когда
    date: Mapped[date_type] = mapped_column(Date, nullable=False)
    time: Mapped[time_type] = mapped_column(Time, nullable=False)

    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    options: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB, nullable=True)

    # аудит статусов
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True))
    cancelled_reason: Mapped[str | None] = mapped_column(Text)

    pet: Mapped["Pet | None"] = relationship(
        "Pet", back_populates="books", lazy="selectin",
    )
    master: Mapped["User | None"] = relationship(
        "User",
        back_populates="books_as_master",
        foreign_keys=[master_id],
        lazy="selectin",
    )
    client: Mapped["User | None"] = relationship(
        "User",
        back_populates="books_as_client",
        foreign_keys=[client_id],
        lazy="selectin",
    )

    services: Mapped[list["BookService"]] = relationship(
        "BookService",
        back_populates="book",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="BookService.id",
    )

    __table_args__ = (
        Index("ix_book_master_date_time", "master_id", "date", "time"),
        Index("ix_book_status_date", "status", "date"),
    )
