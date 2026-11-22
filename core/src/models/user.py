from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.permissions.role_permissions import ROLE_MASK

from .base_model import Base

from src.permissions.enums.roles import Role

if TYPE_CHECKING:
    from .booking import Booking
    from .pet import Pet
    from .refresh_token import RefreshToken
    from .service import Service
    from .slot import Slot
    from .work_schedule import WorkSchedule
    from src.schemas.user import UserLink


class User(Base):
    __tablename__ = "user"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(60), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(25), nullable=False)
    surname: Mapped[str] = mapped_column(String(40), nullable=False)
    patronymic: Mapped[str | None] = mapped_column(String(40))
    phone: Mapped[str | None] = mapped_column(
        String(23), nullable=True, default=None, server_default=None)
    email: Mapped[str | None] = mapped_column(
        String(60), nullable=True, default=None, server_default=None)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, native_enum=False),
        nullable=False,
        default=Role.CLIENT,
        server_default=Role.CLIENT
    )
    permission_mask: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=ROLE_MASK[Role.CLIENT],
        server_default=text(str(ROLE_MASK[Role.CLIENT]))
    )

    pets: Mapped[list["Pet"]] = relationship(
        "Pet",
        back_populates="owner",
        lazy="selectin"
    )

    services: Mapped[list["Service"]] = relationship(
        "Service",
        secondary="master_services",
        lazy="selectin",
        viewonly=True,
    )
    work_schedules: Mapped[list["WorkSchedule"]] = relationship(
        "WorkSchedule",
        back_populates="master",
        lazy="select",
    )
    slots: Mapped[list["Slot"]] = relationship(
        "Slot",
        back_populates="master",
        lazy="select",
    )
    bookings_as_master: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="master",
        foreign_keys="Booking.master_id",
        lazy="select",
    )
    bookings_as_client: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="client",
        foreign_keys="Booking.client_id",
        lazy="select",
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
