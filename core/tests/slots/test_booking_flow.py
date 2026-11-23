"""Интеграционный тест: расчёт слотов → бронь → отмена (на Postgres)."""

import uuid
from datetime import date, time, timedelta

import pytest_asyncio

from src.context import system_context
from src.models.service import Service
from src.models.user import User
from src.models.work_schedule import WorkSchedule
from src.permissions.enums.roles import Role
from src.repositories.uow import SqlAlchemyUnitOfWork
from src.schemas import BookingCreate, SlotsAvailableRequest
from src.services.booking_service import BookingService
from src.services.slot_service import SlotService

DAY = date(2026, 12, 1)


@pytest_asyncio.fixture
async def env(session_factory):
    def uow_factory():
        return SqlAlchemyUnitOfWork(session_factory)

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with system_context():
            service = await uow.repository(Service).create(
                {
                    "title": "Стрижка",
                    "duration": timedelta(hours=1),
                    "price": 1000,
                    "buffer_before_minutes": 0,
                    "buffer_after_minutes": 0,
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
            await uow.repository(WorkSchedule).create(
                {
                    "master_id": master.user_id,
                    "weekday": DAY.weekday(),
                    "start_time": time(9, 0),
                    "end_time": time(12, 0),
                    "is_day_off": False,
                }
            )
        await uow.commit()

    return {
        "uow_factory": uow_factory,
        "service_id": service.service_id,
        "master_id": master.user_id,
    }


async def test_availability_booking_and_cancel(env):
    uow_factory = env["uow_factory"]
    slot_service = SlotService(uow_factory)
    booking_service = BookingService(uow_factory)

    await slot_service.set_interval(30)  # детерминизм между тестами

    available = await slot_service.list_available(
        SlotsAvailableRequest(
            service_id=env["service_id"],
            master_id=env["master_id"],
            date_from=DAY,
        )
    )
    assert available, "должны быть свободные слоты"
    assert len(available) == 5  # 09:00..11:00 с шагом 30
    first = available[0]

    booking = None
    with system_context():
        booking = await booking_service.create(
            BookingCreate(
                master_id=env["master_id"],
                service_id=env["service_id"],
                start_time=first.start_time,
                client_name="Гость",
                client_phone="+70000000000",
            )
        )
    assert booking.start_time == first.start_time
    assert booking.end_time - booking.start_time == timedelta(hours=1)

    # Забронированное время пропадает из доступных.
    after = await slot_service.list_available(
        SlotsAvailableRequest(
            service_id=env["service_id"],
            master_id=env["master_id"],
            date_from=DAY,
        )
    )
    starts = [slot.start_time for slot in after]
    assert first.start_time not in starts

    # После отмены — снова доступно.
    with system_context():
        await booking_service.cancel(booking.booking_id)
    after_cancel = await slot_service.list_available(
        SlotsAvailableRequest(
            service_id=env["service_id"],
            master_id=env["master_id"],
            date_from=DAY,
        )
    )
    starts_after_cancel = [slot.start_time for slot in after_cancel]
    assert first.start_time in starts_after_cancel


async def test_interval_setting_roundtrip(env):
    slot_service = SlotService(env["uow_factory"])
    assert await slot_service.get_interval() == 30
    assert await slot_service.set_interval(45) == 45
    assert await slot_service.get_interval() == 45


async def test_booking_authorized_client_without_phone(env):
    """Авторизованному клиенту телефон не нужен, даже если в профиле он пуст."""
    uow_factory = env["uow_factory"]
    async with uow_factory() as uow:
        with system_context():
            client = await uow.repository(User).create(
                {
                    "login": f"c_{uuid.uuid4().hex[:8]}",
                    "password": "x",
                    "name": "Клиент",
                    "surname": "Безтелефонный",
                    "role": Role.CLIENT,
                }
            )
        await uow.commit()

    slot_service = SlotService(uow_factory)
    booking_service = BookingService(uow_factory)
    await slot_service.set_interval(30)

    available = await slot_service.list_available(
        SlotsAvailableRequest(
            service_id=env["service_id"],
            master_id=env["master_id"],
            date_from=DAY,
        )
    )
    first = available[0]

    with system_context():
        booking = await booking_service.create(
            BookingCreate(
                master_id=env["master_id"],
                service_id=env["service_id"],
                start_time=first.start_time,
                client_id=client.user_id,
            )
        )

    assert booking.client_id == client.user_id
    assert booking.client_phone is None
