from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from .base_schema import Base

from src.models.enums.booking_status import BookingStatus


class BookingRead(Base):
    booking_id: int
    service_id: int
    master_id: int

    start_time: datetime
    end_time: datetime

    client_id: int | None
    pet_id: int | None
    client_name: str | None
    client_phone: str | None

    status: BookingStatus
    comment: str | None
    options: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "booking_id": 1,
                "service_id": 3,
                "master_id": 2,
                "start_time": "2026-11-24T09:00:00+03:00",
                "end_time": "2026-11-24T10:00:00+03:00",
                "client_id": 1,
                "pet_id": 4,
                "client_name": "Иван",
                "client_phone": "+79990001122",
                "status": "pending",
                "comment": "Первый визит",
                "options": {"source": "yandex"},
                "created_at": "2026-11-22T12:00:00",
                "updated_at": "2026-11-22T12:00:00",
            },
        },
    }


class BookingCreate(Base):
    master_id: int = Field(..., examples=[2])
    service_id: int = Field(..., examples=[3])
    start_time: datetime = Field(..., examples=["2026-11-24T09:00:00+03:00"])

    # Либо авторизованный клиент (client_id), либо контакт гостя.
    client_id: int | None = Field(default=None, examples=[1])
    client_name: str | None = Field(default=None, examples=["Иван"])
    client_phone: str | None = Field(default=None, examples=["+79990001122"])

    pet_id: int | None = Field(default=None, examples=[4])
    comment: str | None = Field(default=None, examples=["Первый визит"])
    options: dict[str, Any] | None = Field(
        default=None, examples=[{"source": "yandex"}]
    )

    @model_validator(mode="after")
    def _require_client(self) -> "BookingCreate":
        if self.client_id is None and not (self.client_name and self.client_phone):
            raise ValueError(
                "Укажите client_id или client_name и client_phone"
            )
        return self


class BookingUpdate(Base):
    status: BookingStatus | None = Field(default=None, examples=["confirmed"])
    client_id: int | None = Field(default=None)
    client_name: str | None = Field(default=None)
    client_phone: str | None = Field(default=None)
    pet_id: int | None = Field(default=None)
    comment: str | None = Field(default=None)
    options: dict[str, Any] | None = Field(default=None)
