from datetime import date, datetime

from pydantic import BaseModel, Field


class PetSummary(BaseModel):
    id: int
    name: str
    pet_type_id: int | None = None
    pet_type: str | None = None
    breed_id: int | None = None
    breed: str | None = None
    birthday: date | None = None
    age_years: int | None = None


class AppointmentSummary(BaseModel):
    booking_id: int
    service_id: int
    service_title: str | None = None
    master_id: int
    master_name: str | None = None
    start_time: datetime
    end_time: datetime
    status: str


class UserSummary(BaseModel):
    id: int
    name: str
    phone: str | None = None


class Summary(BaseModel):
    user: UserSummary
    pets: list[PetSummary] = Field(default_factory=list)
    appointments: list[AppointmentSummary] = Field(default_factory=list)
    notes: str | None = None
