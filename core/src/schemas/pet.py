from datetime import date, datetime

from .base_schema import Base


class PetRead(Base):
    pet_id: int
    name: str
    owner_id: int | None
    birthday: date | None
    breed_id: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class PetCreate(Base):
    name: str
    owner_id: int | None = None
    birthday: date | None = None
    breed_id: int | None = None


class PetUpdate(Base):
    name: str | None = None
    owner_id: int | None = None
    birthday: date | None = None
    breed_id: int | None = None
