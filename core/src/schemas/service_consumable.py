from datetime import datetime

from pydantic import Field

from .base_schema import Base
from .storage import StorageRead


class ServiceConsumableRead(Base):
    service_id: int
    consumable_id: int
    volume: int | None
    consumable: StorageRead | None = None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "service_id": 1,
                "consumable_id": 1,
                "volume": 2,
                "consumable": {
                    "item_id": 1,
                    "title": "Шампунь",
                    "measure_unit_id": 1,
                    "count": 10,
                    "created_at": "2026-10-26T10:00:00",
                    "updated_at": "2026-10-26T10:00:00",
                    "who_create": 1,
                    "who_update": 1,
                },
                "created_at": "2026-10-26T10:00:00",
                "updated_at": "2026-10-26T10:00:00",
                "who_create": 1,
                "who_update": 1,
            },
        },
    }


class ServiceConsumableCreate(Base):
    service_id: int = Field(..., examples=[1])
    consumable_id: int = Field(..., examples=[1])
    volume: int | None = Field(default=None, examples=[2])


class ServiceConsumableCreateWithService(Base):
    """Создание строки без service_id — service_id подставит сервис при создании Service."""

    consumable_id: int = Field(
        ...,
        description="ID материала из storage.item_id",
        examples=[1, 2, 3],
    )
    volume: int | None = Field(
        default=None,
        description="Количество материала",
        examples=[1, 5],
    )

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {"consumable_id": 1, "volume": 2},
        },
    }


class ServiceConsumableUpdate(Base):
    service_id: int | None = Field(default=None, examples=[1])
    consumable_id: int | None = Field(default=None, examples=[1])
    volume: int | None = Field(default=None, examples=[2])
