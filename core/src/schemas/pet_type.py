from datetime import datetime

from pydantic import Field

from .base_schema import Base


class PetTypeRead(Base):
    pet_type_id: int
    title: str

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "pet_type_id": 1,
                "title": "Собака",
                "created_at": "2026-10-26T10:00:00",
                "updated_at": "2026-10-26T10:00:00",
                "who_create": 1,
                "who_update": 1,
            },
        },
    }


class PetTypeCreate(Base):
    title: str = Field(..., examples=["Собака"])


class PetTypeUpdate(Base):
    title: str | None = Field(default=None, examples=["Собака"])
