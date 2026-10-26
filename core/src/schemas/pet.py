from datetime import date, datetime

from pydantic import Field

from .base_schema import Base


class PetRead(Base):
    pet_id: int
    name: str
    owner_id: int | None
    birthday: date | None
    breed_id: int | None

    created_at: datetime
    updated_at: datetime
    who_create: int | None
    who_update: int | None

    model_config = Base.model_config | {
        "json_schema_extra": {
            "example": {
                "pet_id": 1,
                "name": "Бобик",
                "owner_id": 1,
                "birthday": "2020-05-15",
                "breed_id": 1,
                "created_at": "2026-10-26T10:00:00",
                "updated_at": "2026-10-26T10:00:00",
                "who_create": 1,
                "who_update": 1,
            },
        },
    }


class PetCreate(Base):
    name: str = Field(..., examples=["Бобик"])
    owner_id: int | None = Field(default=None, examples=[1])
    birthday: date | None = Field(default=None, examples=["2020-05-15"])
    breed_id: int | None = Field(default=None, examples=[1])


class PetUpdate(Base):
    name: str | None = Field(default=None, examples=["Бобик"])
    owner_id: int | None = Field(default=None, examples=[1])
    birthday: date | None = Field(default=None, examples=["2020-05-15"])
    breed_id: int | None = Field(default=None, examples=[1])
