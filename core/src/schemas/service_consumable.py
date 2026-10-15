from datetime import datetime

from .base_schema import Base


class ServiceConsumableRead(Base):
    service_id: int
    consumable_id: int
    volume: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class ServiceConsumableCreate(Base):
    service_id: int
    consumable_id: int
    volume: int | None = None


class ServiceConsumableUpdate(Base):
    service_id: int | None = None
    consumable_id: int | None = None
    volume: int | None = None
