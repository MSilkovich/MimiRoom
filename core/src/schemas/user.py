from datetime import datetime

from src.permissions.enums.roles import Role

from .base_schema import Base


class UserRead(Base):
    user_id: int
    login: str
    name: str
    surname: str
    patronymic: str | None
    role: str

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class UserCreate(Base):
    login: str
    password: str
    name: str
    surname: str
    patronymic: str | None = None


class UserUpdate(Base):
    login: str | None = None
    password: str | None = None
    name: str | None = None
    surname: str | None = None
    patronymic: str | None = None


class UserRoleUpdate(Base):
    role: Role | None = None
