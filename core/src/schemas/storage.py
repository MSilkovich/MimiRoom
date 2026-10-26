from datetime import datetime

from pydantic import Field

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

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "item_id": 1,
                "title": "Шампунь",
                "measure_unit_id": 1,
                "count": 10,
                "created_at": "2026-10-26T10:00:00",
                "updated_at": "2026-10-26T10:00:00",
                "who_create": 1,
                "who_update": 1,
            },
        },
    }


class StorageCreate(Base):
    title: str | None = Field(default=None, examples=["Шампунь"])
    measure_unit_id: int | None = Field(default=None, examples=[1])
    count: int | None = Field(default=None, examples=[10])


class StorageUpdate(Base):
    title: str | None = Field(default=None, examples=["Шампунь"])
    measure_unit_id: int | None = Field(default=None, examples=[1])
    count: int | None = Field(default=None, examples=[10])
