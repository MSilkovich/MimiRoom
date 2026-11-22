from datetime import date, datetime

from pydantic import Field

from .base_schema import Base

from src.models.enums.slot_status import SlotStatus


class SlotRead(Base):
    slot_id: int
    master_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    status: SlotStatus
    # Заполняется в выдаче доступности: свободен ли слот с учётом пересечений.
    available: bool | None = None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "slot_id": 1,
                "master_id": 1,
                "service_id": 3,
                "start_time": "2026-11-24T09:00:00+03:00",
                "end_time": "2026-11-24T10:00:00+03:00",
                "status": "free",
                "available": True,
            },
        },
    }


class SlotGenerateRequest(Base):
    master_id: int = Field(..., examples=[1])
    service_id: int = Field(..., examples=[3])
    date_from: date = Field(..., examples=["2026-11-24"])
    date_to: date = Field(..., examples=["2026-11-30"])
    step_minutes: int | None = Field(
        default=None,
        ge=1,
        description=(
            "Шаг сетки в минутах. По умолчанию — длительность услуги с буферами."
        ),
        examples=[None, 30],
    )


class SlotGenerateResponse(Base):
    created: int
    slots: list[SlotRead] = Field(default_factory=list)
