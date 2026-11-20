from datetime import datetime

from pydantic import Field

from .base_schema import Base


class MeasureUnitRead(Base):
    measure_unit_id: int
    title: str | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "measure_unit_id": 1,
                "title": "мл",
            },
        },
    }


class MeasureUnitCreate(Base):
    title: str | None = Field(default=None, examples=["мл"])


class MeasureUnitUpdate(Base):
    title: str | None = Field(default=None, examples=["мл"])
