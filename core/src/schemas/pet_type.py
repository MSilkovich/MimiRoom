from datetime import datetime

from pydantic import Field

from .base_schema import Base


class PetTypeRead(Base):
    pet_type_id: int
    title: str

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "pet_type_id": 1,
                "title": "Собака",
            },
        },
    }


class PetTypeCreate(Base):
    title: str = Field(..., examples=["Собака"])


class PetTypeUpdate(Base):
    title: str | None = Field(default=None, examples=["Собака"])
