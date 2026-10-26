from datetime import datetime

from pydantic import Field

from .base_schema import Base


class BreedRead(Base):
    breed_id: int
    title: str | None
    pet_type_id: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "breed_id": 1,
                "title": "Лабрадор",
                "pet_type_id": 1,
                "created_at": "2026-10-26T10:00:00",
                "updated_at": "2026-10-26T10:00:00",
                "who_create": 1,
                "who_update": 1,
            },
        },
    }


class BreedCreate(Base):
    title: str | None = Field(default=None, examples=["Лабрадор"])
    pet_type_id: int | None = Field(default=None, examples=[1])


class BreedUpdate(Base):
    title: str | None = Field(default=None, examples=["Лабрадор"])
    pet_type_id: int | None = Field(default=None, examples=[1])
