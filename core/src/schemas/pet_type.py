from datetime import datetime

from .base_schema import Base


class PetTypeRead(Base):
    pet_type_id: int
    title: str

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class PetTypeCreate(Base):
    title: str


class PetTypeUpdate(Base):
    title: str | None = None
