from datetime import datetime

from pydantic import Field

from .base_schema import Base
from .slot import SlotRead

from src.models.enums.booking_status import BookingStatus


class BookingRead(Base):
    booking_id: int
    slot_id: int
    service_id: int
    resource_id: int
    client_name: str
    client_phone: str
    status: BookingStatus
    comment: str | None
    created_at: datetime
    updated_at: datetime
    slot: SlotRead | None = None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "booking_id": 1,
                "slot_id": 10,
                "service_id": 3,
                "resource_id": 1,
                "client_name": "Иван",
                "client_phone": "+79990001122",
                "status": "pending",
                "comment": "Первый визит",
                "created_at": "2026-11-22T12:00:00",
                "updated_at": "2026-11-22T12:00:00",
                "slot": None,
            },
        },
    }


class BookingCreate(Base):
    slot_id: int = Field(..., examples=[10])
    client_name: str = Field(..., examples=["Иван"])
    client_phone: str = Field(..., examples=["+79990001122"])
    comment: str | None = Field(default=None, examples=["Первый визит"])


class BookingUpdate(Base):
    status: BookingStatus | None = Field(default=None, examples=["confirmed"])
    client_name: str | None = Field(default=None)
    client_phone: str | None = Field(default=None)
    comment: str | None = Field(default=None)
