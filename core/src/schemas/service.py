from datetime import datetime, timedelta
from decimal import Decimal

from pydantic import Field, computed_field

from .base_schema import Base
from .service_consumable import (
    ServiceConsumableCreateWithService,
    ServiceConsumableRead,
)


class ServiceRead(Base):
    service_id: int
    title: str
    duration: timedelta | None
    price: Decimal
    breed_id: int | None
    consumables: list[ServiceConsumableRead] = Field(default_factory=list)

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None

    @computed_field
    @property
    def duration_minutes(self) -> int | None:
        """Длительность в минутах — удобно для клиента (не нужно парсить ISO 8601)."""
        if self.duration is None:
            return None
        return int(self.duration.total_seconds() // 60)

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "service_id": 1,
                "title": "Стрижка",
                "duration": "PT1H30M",
                "duration_minutes": 90,
                "price": "1500.00",
                "breed_id": 1,
                "consumables": [
                    {"consumable_id": 1, "volume": 2},
                    {"consumable_id": 2, "volume": 1},
                ],
                "created_at": "2026-10-26T10:00:00",
                "updated_at": "2026-10-26T10:00:00",
                "who_create": 1,
                "who_update": 1,
            },
        },
    }


class ServiceCreate(Base):
    title: str = Field(..., examples=["Стрижка"])
    duration: timedelta | None = Field(
        default=None,
        description="Длительность в ISO 8601 (например, PT1H30M = 1ч30м, P3D = 3 дня)",
        examples=["PT1H30M", "PT45M", "P1D"],
    )
    price: Decimal = Field(..., examples=["1500.00"])
    breed_id: int | None = Field(default=None, examples=[1])
    consumables: list[ServiceConsumableCreateWithService] = Field(
        default_factory=list,
        description="Список материалов, списываемых при оказании услуги",
        examples=[
            [
                {"consumable_id": 1, "volume": 1},
                {"consumable_id": 2, "volume": 3},
            ],
        ],
    )


class ServiceUpdate(Base):
    title: str | None = Field(default=None, examples=["Стрижка"])
    duration: timedelta | None = Field(
        default=None,
        description="Длительность в ISO 8601 (например, PT1H30M = 1ч30м, P3D = 3 дня)",
        examples=["PT1H30M", "PT45M", "P1D"],
    )
    price: Decimal | None = Field(default=None, examples=["1500.00"])
    breed_id: int | None = Field(default=None, examples=[1])
