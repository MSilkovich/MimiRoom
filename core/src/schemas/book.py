from datetime import date as date_type, datetime, time as time_type

from .base_schema import Base


class BookRead(Base):
    book_id: int
    pet_id: int | None
    master_id: int | None
    date: date_type | None
    time: time_type | None
    service_id: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class BookCreate(Base):
    pet_id: int | None = None
    master_id: int | None = None
    date: date_type | None = None
    time: time_type | None = None
    service_id: int | None = None


class BookUpdate(Base):
    pet_id: int | None = None
    master_id: int | None = None
    date: date_type | None = None
    time: time_type | None = None
    service_id: int | None = None