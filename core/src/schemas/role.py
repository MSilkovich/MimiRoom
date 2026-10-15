from datetime import datetime

from .base_schema import Base


class RoleRead(Base):
    role_id: int
    title: str

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class RoleCreate(Base):
    title: str


class RoleUpdate(Base):
    title: str | None = None
