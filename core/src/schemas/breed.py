from datetime import datetime

from pydantic import Field

from .base_schema import Base


class BreedRead(Base):
    breed_id: int
    title: str | None
    pet_type_id: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "breed_id": 1,
                "title": "Лабрадор",
                "pet_type_id": 1,
            },
        },
    }


class BreedCreate(Base):
    title: str | None = Field(default=None, examples=["Лабрадор"])
    pet_type_id: int | None = Field(default=None, examples=[1])


class BreedUpdate(Base):
    title: str | None = Field(default=None, examples=["Лабрадор"])
    pet_type_id: int | None = Field(default=None, examples=[1])
