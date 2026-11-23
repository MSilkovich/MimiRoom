"""Интеграционный тест расширенной сводки пользователя (summary)."""

import uuid
from datetime import date, datetime, time, timedelta, timezone

import pytest_asyncio

from src.context import system_context
from src.models.breed import Breed
from src.models.pet import Pet
from src.models.pet_type import PetType
from src.models.service import Service
from src.models.user import User
from src.permissions.enums.roles import Role
from src.repositories.uow import SqlAlchemyUnitOfWork

FUTURE = datetime.now(timezone.utc) + timedelta(days=30)


@pytest_asyncio.fixture
async def summary_env(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with system_context():
            pet_type = await uow.repository(PetType).create({"title": "Собака"})
            breed = await uow.repository(Breed).create(
                {"title": "средняя", "pet_type_id": pet_type.pet_type_id}
            )
            client = await uow.repository(User).create(
                {
                    "login": f"c_{uuid.uuid4().hex[:8]}",
                    "password": "x",
                    "name": "Клиент",
                    "surname": "Тестов",
                    "role": Role.CLIENT,
                }
            )
            pet = await uow.repository(Pet).create(
                {
                    "name": "Бобик",
                    "owner_id": client.user_id,
                    "breed_id": breed.breed_id,
                    "birthday": date(2020, 1, 1),
                }
            )
            service = await uow.repository(Service).create(
                {
                    "title": "Стрижка",
                    "duration": timedelta(hours=1),
                    "price": 1000,
                }
            )
            master = await uow.repository(User).create(
                {
                    "login": f"m_{uuid.uuid4().hex[:8]}",
                    "password": "x",
                    "name": "Мастер",
                    "surname": "Тестов",
                    "role": Role.GROOMER,
                }
            )
            await uow.repository(User).replace_master_services(
                master.user_id, [service.service_id]
            )
            from src.models.booking import Booking
            from src.models.enums.booking_status import BookingStatus

            await uow.repository(Booking).create(
                {
                    "service_id": service.service_id,
                    "master_id": master.user_id,
                    "start_time": FUTURE,
                    "end_time": FUTURE + timedelta(hours=1),
                    "client_id": client.user_id,
                    "pet_id": pet.pet_id,
                    "client_name": "Клиент Тестов",
                    "client_phone": "+70000000000",
                    "status": BookingStatus.PENDING,
                }
            )
        await uow.commit()

    return {
        "session_factory": session_factory,
        "client_id": client.user_id,
        "pet_id": pet.pet_id,
        "breed_id": breed.breed_id,
        "pet_type_id": pet_type.pet_type_id,
        "service_id": service.service_id,
    }


async def test_summary_has_pet_details_and_appointments(summary_env):
    async with SqlAlchemyUnitOfWork(summary_env["session_factory"]) as uow:
        summary = await uow.repository(User).get_summary_by_id(
            summary_env["client_id"]
        )

    assert summary is not None
    assert summary.pets, "питомцы должны быть в сводке"
    pet = summary.pets[0]
    assert pet.name == "Бобик"
    assert pet.breed_id == summary_env["breed_id"]
    assert pet.pet_type_id == summary_env["pet_type_id"]
    assert pet.breed == "средняя"
    assert pet.pet_type == "Собака"
    assert pet.age_years is not None and pet.age_years >= 4

    assert len(summary.appointments) == 1
    appt = summary.appointments[0]
    assert appt.service_id == summary_env["service_id"]
    assert appt.service_title == "Стрижка"
    assert appt.master_name == "Мастер Тестов"
    assert appt.status == "pending"
