from datetime import date, datetime

from pydantic import Field

from .base_schema import Base


class SlotRead(Base):
    """Расчётный слот (не хранится в БД).

    Возможное время для новой записи: ``start_time``/``end_time`` интервала
    услуги и конкретный ``master_id``, к которому относится слот.
    """

    master_id: int
    service_id: int
    start_time: datetime
    end_time: datetime
    available: bool = True

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "master_id": 1,
                "service_id": 3,
                "start_time": "2026-11-24T09:00:00+03:00",
                "end_time": "2026-11-24T10:00:00+03:00",
                "available": True,
            },
        },
    }


class SlotsAvailableRequest(Base):
    """Запрос расчёта свободных слотов (параметры — в теле, не в query)."""

    service_id: int = Field(..., examples=[3])
    master_id: int | None = Field(
        default=None,
        description="Если не задан — мастера подбирает сервер",
        examples=[1, None],
    )
    date_from: date = Field(..., examples=["2026-11-24"])
    date_to: date | None = Field(default=None, examples=["2026-11-30"])
    pet_id: int | None = Field(
        default=None,
        description="Питомец (задел под расчёт длительности/цены)",
        examples=[4],
    )


class SlotIntervalUpdate(Base):
    interval_minutes: int = Field(..., ge=1, le=1440, examples=[30])


class SlotIntervalRead(Base):
    interval_minutes: int = Field(..., examples=[30])
