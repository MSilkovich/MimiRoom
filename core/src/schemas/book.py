from datetime import date as date_type, datetime, time as time_type
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from .base_schema import Base

from src.models.enums.book_source import BookSource
from src.models.enums.book_status import BookStatus


class BookServiceRead(BaseModel):
    id: int
    service_id: int
    master_id: int | None
    service_name: str
    price_at_booking: Decimal

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "id": 10,
                "service_id": 3,
                "master_id": 2,
                "service_name": "Стрижка кошки",
                "price_at_booking": "1500.00",
            },
        },
    }


class BookServiceCreate(BaseModel):
    service_id: int = Field(examples=[3])
    master_id: int | None = Field(default=None, examples=[2])


class BookRead(Base):
    book_id: int
    status: BookStatus
    source: BookSource | None

    pet_id: int | None
    master_id: int | None
    client_id: int | None

    date: date_type
    time: time_type
    comment: str | None
    options: dict[str, Any] | None

    services: list[BookServiceRead] = []

    confirmed_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    cancelled_reason: str | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "book_id": 1,
                "status": "pending",
                "source": "website",
                "pet_id": 1,
                "master_id": 2,
                "client_id": None,
                "date": "2026-11-01",
                "time": "14:30:00",
                "comment": "Первый визит",
                "options": {"call_before": "30m"},
                "services": [
                    {
                        "id": 10,
                        "service_id": 3,
                        "master_id": 2,
                        "service_name": "Стрижка кошки",
                        "price_at_booking": "1500.00",
                    },
                ],
                "confirmed_at": None,
                "completed_at": None,
                "cancelled_at": None,
                "cancelled_reason": None,
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
    client_id: int | None = Field(default=None, examples=[None])
    source: BookSource | None = Field(default=None, examples=["website"])

    date: date_type = Field(examples=["2026-11-01"])
    time: time_type = Field(examples=["14:30:00"])
    comment: str | None = Field(default=None, examples=["Первый визит"])
    options: dict[str, Any] | None = Field(
        default=None, examples=[{"call_before": "30m"}])

    services: list[BookServiceCreate] = Field(default_factory=list)


class BookUpdate(Base):
    pet_id: int | None = Field(default=None, examples=[1])
    master_id: int | None = Field(default=None, examples=[2])
    client_id: int | None = Field(default=None)
    source: BookSource | None = Field(default=None)
    status: BookStatus | None = Field(default=None)

    date: date_type | None = Field(default=None, examples=["2026-11-01"])
    time: time_type | None = Field(default=None, examples=["14:30:00"])
    comment: str | None = Field(default=None, examples=["Первый визит"])
    options: dict[str, Any] | None = Field(default=None)

    services: list[BookServiceCreate] | None = None
