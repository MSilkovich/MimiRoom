from datetime import datetime

from .base_schema import Base


class UserRead(Base):
    user_id: int
    login: str
    name: str
    surname: str
    patronymic: str | None
    role_id: int | None

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
    role_id: int | None = None


class UserUpdate(Base):
    login: str | None = None
    password: str | None = None
    name: str | None = None
    surname: str | None = None
    patronymic: str | None = None
    role_id: int | None = None
