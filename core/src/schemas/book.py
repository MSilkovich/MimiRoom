from datetime import date as date_type, datetime, time as time_type

from pydantic import Field

from .base_schema import Base


class BookRead(Base):
    book_id: int
    pet_id: int | None
    master_id: int | None
    date: date_type | None
    time: time_type | None
    service_id: int | None
    comment: str | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "book_id": 1,
                "pet_id": 1,
                "master_id": 2,
                "date": "2026-11-01",
                "time": "14:30:00",
                "service_id": 3,
                "comment": "Первый визит",
                "created_at": "2026-10-26T10:00:00",
                "updated_at": "2026-10-26T10:00:00",
                "who_create": 1,
                "who_update": 1,
            },
        },
    }


class BookCreate(Base):
    pet_id: int | None = Field(default=None, examples=[1])
    master_id: int | None = Field(default=None, examples=[2])
    date: date_type | None = Field(default=None, examples=["2026-11-01"])
    time: time_type | None = Field(default=None, examples=["14:30:00"])
    service_id: int | None = Field(default=None, examples=[3])
    comment: str | None = Field(default=None, examples=["Первый визит"])


class BookUpdate(Base):
    pet_id: int | None = Field(default=None, examples=[1])
    master_id: int | None = Field(default=None, examples=[2])
    date: date_type | None = Field(default=None, examples=["2026-11-01"])
    time: time_type | None = Field(default=None, examples=["14:30:00"])
    service_id: int | None = Field(default=None, examples=[3])
    comment: str | None = Field(default=None, examples=["Первый визит"])
