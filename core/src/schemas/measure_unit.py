from datetime import datetime

from .base_schema import Base


class MeasureUnitRead(Base):
    measure_unit_id: int
    title: str | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None


class MeasureUnitCreate(Base):
    title: str | None = None


class MeasureUnitUpdate(Base):
    title: str | None = None
