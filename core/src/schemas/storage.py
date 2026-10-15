from datetime import datetime

from .base_schema import Base


class StorageRead(Base):
    item_id: int
    title: str | None
    measure_unit_id: int | None
    count: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class StorageCreate(Base):
    title: str | None = None
    measure_unit_id: int | None = None
    count: int | None = None


class StorageUpdate(Base):
    title: str | None = None
    measure_unit_id: int | None = None
    count: int | None = None
