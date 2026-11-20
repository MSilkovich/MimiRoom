from pydantic import BaseModel, Field


class PetSummary(BaseModel):
    id: int
    name: str
    pet_type: str | None = None
    breed: str | None = None


class UserSummary(BaseModel):
    id: int
    name: str
    phone: str | None = None


class Summary(BaseModel):
    user: UserSummary
    pets: list[PetSummary] = Field(default_factory=list)
    notes: str | None = None
