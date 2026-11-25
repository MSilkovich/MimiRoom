from datetime import datetime

from pydantic import Field

from src.permissions.enums.roles import Role

from .base_schema import Base
from .pet import PetRead


class UserRead(Base):
    user_id: int
    login: str
    name: str
    surname: str
    patronymic: str | None
    phone: str | None
    email: str | None
    role: str


class UserProfileRead(UserRead):
    """Профиль пользователя для ЛК: данные + его питомцы."""

    pets: list[PetRead] = Field(default_factory=list)


class UserCreate(Base):
    login: str
    password: str
    name: str
    surname: str
    patronymic: str | None = None
    phone: str | None
    email: str | None


class UserUpdate(Base):
    login: str | None = None
    password: str | None = None
    name: str | None = None
    surname: str | None = None
    patronymic: str | None = None
    phone: str | None
    email: str | None


class UserRoleUpdate(Base):
    role: Role | None = None
