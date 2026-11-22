from datetime import time as time_type

from pydantic import Field

from .base_schema import Base


class WorkScheduleRead(Base):
    work_schedule_id: int
    master_id: int
    weekday: int
    start_time: time_type
    end_time: time_type
    is_day_off: bool

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "work_schedule_id": 1,
                "master_id": 1,
                "weekday": 0,
                "start_time": "09:00:00",
                "end_time": "18:00:00",
                "is_day_off": False,
            },
        },
    }


class WorkScheduleCreate(Base):
    master_id: int = Field(..., examples=[1])
    weekday: int = Field(..., ge=0, le=6, examples=[0])
    start_time: time_type = Field(..., examples=["09:00:00"])
    end_time: time_type = Field(..., examples=["18:00:00"])
    is_day_off: bool = Field(default=False, examples=[False])


class WorkScheduleUpdate(Base):
    weekday: int | None = Field(default=None, ge=0, le=6, examples=[0])
    start_time: time_type | None = Field(default=None, examples=["09:00:00"])
    end_time: time_type | None = Field(default=None, examples=["18:00:00"])
    is_day_off: bool | None = Field(default=None, examples=[False])
