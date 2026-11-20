from datetime import datetime

from pydantic import Field

from .base_schema import Base


class StorageRead(Base):
    item_id: int
    title: str | None
    measure_unit_id: int | None
    count: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "item_id": 1,
                "title": "Шампунь",
                "measure_unit_id": 1,
                "count": 10,
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
