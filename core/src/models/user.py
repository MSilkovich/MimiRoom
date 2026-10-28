from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from .base_model import Base

from src.permissions.enums.roles import Role

if TYPE_CHECKING:
    from .book import Book
    from .pet import Pet
    from .refresh_token import RefreshToken
    from src.schemas.user import UserLink


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(60), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    surname: Mapped[str] = mapped_column(String(40), nullable=False)
    patronymic: Mapped[str | None] = mapped_column(String(40))
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, native_enum=False),
        nullable=False,
        default=Role.CLIENT,
        server_default=Role.CLIENT
    )
    permission_mask: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
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

    links: Mapped[list["UserLink"]] = relationship(
        "UserLink",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
