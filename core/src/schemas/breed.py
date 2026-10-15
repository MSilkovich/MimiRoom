from datetime import datetime

from .base_schema import Base


class BreedRead(Base):
    breed_id: int
    title: str | None
    pet_type_id: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class BreedCreate(Base):
    title: str | None = None
    pet_type_id: int | None = None


class BreedUpdate(Base):
    title: str | None = None
    pet_type_id: int | None = None
