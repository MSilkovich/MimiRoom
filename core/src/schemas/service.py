from datetime import datetime, timedelta
from decimal import Decimal

from .base_schema import Base


class ServiceRead(Base):
    service_id: int
    title: str
    duration: timedelta | None
    price: Decimal
    breed_id: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class ServiceCreate(Base):
    title: str
    duration: timedelta | None = None
    price: Decimal
    breed_id: int | None = None


class ServiceUpdate(Base):
    title: str | None = None
    duration: timedelta | None = None
    price: Decimal | None = None
    breed_id: int | None = None
