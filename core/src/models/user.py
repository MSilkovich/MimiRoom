from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base_model import Base

if TYPE_CHECKING:
    from .book import Book
    from .pet import Pet
    from .role import Role
    from .refresh_token import RefreshToken


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(60), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    surname: Mapped[str] = mapped_column(String(40), nullable=False)
    patronymic: Mapped[str | None] = mapped_column(String(40))
    role_id: Mapped[int | None] = mapped_column(
        "role",
        ForeignKey("role.role_id")
    )

    role: Mapped["Role | None"] = relationship(
        "Role",
        back_populates="users",
        lazy="selectin"
    )
    pets: Mapped[list["Pet"]] = relationship(
        "Pet",
        back_populates="owner",
        lazy="selectin"
    )
    books: Mapped[list["Book"]] = relationship(
        "Book",
        back_populates="master",
        lazy="selectin"
    )

    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )
