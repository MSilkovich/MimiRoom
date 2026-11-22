from datetime import datetime
from typing import Any

from pydantic import Field, model_validator

from .base_schema import Base
from .slot import SlotRead

from src.models.enums.booking_status import BookingStatus


class BookingRead(Base):
    booking_id: int
    slot_id: int
    service_id: int
    master_id: int

    client_id: int | None
    pet_id: int | None
    client_name: str | None
    client_phone: str | None

    status: BookingStatus
    comment: str | None
    options: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    slot: SlotRead | None = None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "booking_id": 1,
                "slot_id": 10,
                "service_id": 3,
                "master_id": 2,
                "client_id": 1,
                "pet_id": 4,
                "client_name": "Иван",
                "client_phone": "+79990001122",
                "status": "pending",
                "comment": "Первый визит",
                "options": {"source": "yandex"},
                "created_at": "2026-11-22T12:00:00",
                "updated_at": "2026-11-22T12:00:00",
                "slot": None,
            },
        },
    }


class BookingCreate(Base):
    slot_id: int = Field(..., examples=[10])

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
