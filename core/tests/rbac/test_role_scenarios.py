"""Интеграционные сценарии RBAC: разные роли и границы OWN-доступа.

Тесты работают на реальном PostgreSQL (как и остальные integration-тесты core):
Service -> UnitOfWork -> Repository, плюс реальные permission-зависимости
из ``src.dependencies``. HTTP-слой здесь не поднимается, чтобы не тащить
дополнительные зависимости (httpx) и не дублировать auth-middleware.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio

from src.context import system_context
from src.dependencies import require_perm, require_role, require_service
from src.excpetions.auth import PermissionDeniedError
from src.excpetions.crud import NotFoundError
from src.middleware.principal import Principal, PrincipalKind
from src.models import Booking, Pet, Service, User, WorkSchedule
from src.models.enums.booking_status import BookingStatus
from src.permissions.enums.permissions import Permission
from src.permissions.enums.roles import Role
from src.permissions.enums.scope import Scope
from src.permissions.role_permissions import ROLE_MASK
from src.repositories.uow import SqlAlchemyUnitOfWork
from src.schemas import BookingCreate, PetCreate, PetUpdate
from src.services import (
    BookingService,
    MeasureUnitService,
    PetService,
    UserService,
    WorkScheduleService,
)
from src.services.slot_generator import get_default_tz
from src.schemas import MeasureUnitCreate

DAY = date.today() + timedelta(days=7)


def _fake_user(role: Role, user_id: int) -> User:
    """User без БД нужен только для проверки permission-зависимости."""
    return User(
        user_id=user_id,
        login=f"fake_{role.value}_{user_id}",
        password="x",
        name="Fake",
        surname="User",
        role=role,
        permission_mask=ROLE_MASK[role],
    )


async def _rule(
    role: Role | None,
    permission: Permission,
    *,
    user_id: int = 1,
    min_scope: Scope = Scope.OWN,
    owner_field: str = "who_create",
    allow_service: bool = False,
):
    """Получить PermissionRule тем же механизмом, что и роутеры."""
    dependency = require_perm(
        permission,
        min_scope=min_scope,
        owner_field=owner_field,
        allow_service=allow_service,
    )
    if role is None:
        principal = Principal(kind=PrincipalKind.SERVICE)
    else:
        principal = Principal(
            kind=PrincipalKind.USER, user=_fake_user(role, user_id)
        )
    return await dependency(principal)


@pytest_asyncio.fixture
async def env(session_factory):
    """Данные для сценариев: 4 роли, услуга, графики, питомцы и записи."""
    uniq = uuid.uuid4().hex[:8]

    def uow_factory():
        return SqlAlchemyUnitOfWork(session_factory)

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with system_context(fake_user_id=1000):
            async def make_user(role: Role, label: str) -> User:
                return await uow.repository(User).create(
                    {
                        "login": f"{label}_{uniq}",
                        "password": "x",
                        "name": label.title()[:25],
                        "surname": "Test",
                        "role": role,
                        "permission_mask": ROLE_MASK[role],
                    }
                )

            admin = await make_user(Role.ADMIN, "admin")
            manager = await make_user(Role.MANAGER, "manager")
            groomer = await make_user(Role.GROOMER, "groomer")
            groomer2 = await make_user(Role.GROOMER, "groomer2")
            client = await make_user(Role.CLIENT, "client")
            client2 = await make_user(Role.CLIENT, "client2")

            service = await uow.repository(Service).create(
                {
                    "title": f"Стрижка {uniq}",
                    "description": "Тестовая услуга",
                    "duration": timedelta(hours=1),
                    "price": Decimal("1000.00"),
                    "buffer_before_minutes": 0,
                    "buffer_after_minutes": 0,
                }
            )
            await uow.repository(Service).replace_masters(
                service.service_id, [groomer.user_id, groomer2.user_id]
            )

            schedule = await uow.repository(WorkSchedule).create(
                {
                    "master_id": groomer.user_id,
                    "weekday": DAY.weekday(),
                    "start_time": time(9, 0),
                    "end_time": time(18, 0),
                    "is_day_off": False,
                }
            )
            schedule2 = await uow.repository(WorkSchedule).create(
                {
                    "master_id": groomer2.user_id,
                    "weekday": DAY.weekday(),
                    "start_time": time(9, 0),
                    "end_time": time(18, 0),
                    "is_day_off": False,
                }
            )

            pet_client = await uow.repository(Pet).create(
                {"name": f"Бобик{uniq}", "owner_id": client.user_id}
            )
            pet_other = await uow.repository(Pet).create(
                {"name": f"Мурка{uniq}", "owner_id": client2.user_id}
            )

            tz = get_default_tz()
            base = datetime.combine(DAY, time(10, 0), tzinfo=tz)
            booking_client = await uow.repository(Booking).create(
                {
                    "service_id": service.service_id,
                    "master_id": groomer.user_id,
                    "start_time": base,
                    "end_time": base + timedelta(hours=1),
                    "client_id": client.user_id,
                    "pet_id": pet_client.pet_id,
                    "client_name": "Client Test",
                    "client_phone": "+70000000001",
                    "status": BookingStatus.PENDING,
                }
            )
            booking_other = await uow.repository(Booking).create(
                {
                    "service_id": service.service_id,
                    "master_id": groomer2.user_id,
                    "start_time": base,
                    "end_time": base + timedelta(hours=1),
                    "client_id": client2.user_id,
                    "pet_id": pet_other.pet_id,
                    "client_name": "Client2 Test",
                    "client_phone": "+70000000002",
                    "status": BookingStatus.PENDING,
                }
            )
            booking_for_groomer = await uow.repository(Booking).create(
                {
                    "service_id": service.service_id,
                    "master_id": groomer.user_id,
                    "start_time": base + timedelta(hours=1),
                    "end_time": base + timedelta(hours=2),
                    "client_id": client2.user_id,
                    "pet_id": pet_other.pet_id,
                    "client_name": "Client2 Test",
                    "client_phone": "+70000000002",
                    "status": BookingStatus.PENDING,
                }
            )

        await uow.commit()

    return {
        "uow_factory": uow_factory,
        "admin": admin,
        "manager": manager,
        "groomer": groomer,
        "groomer2": groomer2,
        "client": client,
        "client2": client2,
        "service": service,
        "schedule": schedule,
        "schedule2": schedule2,
        "pet_client": pet_client,
        "pet_other": pet_other,
        "booking_client": booking_client,
        "booking_other": booking_other,
        "booking_for_groomer": booking_for_groomer,
    }


async def test_client_sees_only_own_pets_and_cannot_touch_foreign(env):
    client = env["client"]
    pet_service = PetService(env["uow_factory"])
    rule = await _rule(
        Role.CLIENT, Permission.PET_READ, user_id=client.user_id, owner_field="owner_id"
    )

    pets = await pet_service.get_multi(rule=rule)
    pet_ids = {pet.pet_id for pet in pets}

    assert env["pet_client"].pet_id in pet_ids
    assert env["pet_other"].pet_id not in pet_ids
    assert await pet_service.get(env["pet_other"].pet_id, rule=rule) is None

    with pytest.raises(NotFoundError):
        await pet_service.update(
            env["pet_other"].pet_id, PetUpdate(name="Взлом"), rule=rule
        )

    with system_context(fake_user_id=client.user_id):
        created = await pet_service.create(
            PetCreate(name="Новый", owner_id=env["client2"].user_id), rule=rule
        )
    assert created.owner_id == client.user_id

    with pytest.raises(NotFoundError):
        await pet_service.get_history(env["pet_other"].pet_id, rule=rule)


async def test_client_booking_isolation_and_owner_enforcement(env):
    client = env["client"]
    booking_service = BookingService(env["uow_factory"])
    read_rule = await _rule(
        Role.CLIENT,
        Permission.BOOK_READ,
        user_id=client.user_id,
        owner_field="client_id",
    )
    write_rule = await _rule(
        Role.CLIENT,
        Permission.BOOK_WRITE,
        user_id=client.user_id,
        owner_field="client_id",
    )
    cancel_rule = await _rule(
        Role.CLIENT,
        Permission.BOOK_CANCEL,
        user_id=client.user_id,
        owner_field="client_id",
    )

    items = await booking_service.get_multi(rule=read_rule)
    ids = {booking.booking_id for booking in items}
    assert env["booking_client"].booking_id in ids
    assert env["booking_other"].booking_id not in ids
    assert await booking_service.get(env["booking_other"].booking_id, rule=read_rule) is None

    start = datetime.combine(DAY, time(13, 0), tzinfo=get_default_tz())
    with pytest.raises(PermissionDeniedError):
        await booking_service.create(
            BookingCreate(
                master_id=env["groomer"].user_id,
                service_id=env["service"].service_id,
                start_time=start,
                client_id=env["client2"].user_id,
            ),
            rule=write_rule,
        )

    with system_context(fake_user_id=client.user_id):
        own = await booking_service.create(
            BookingCreate(
                master_id=env["groomer"].user_id,
                service_id=env["service"].service_id,
                start_time=start,
                client_id=client.user_id,
            ),
            rule=write_rule,
        )
    assert own.client_id == client.user_id

    with pytest.raises(PermissionDeniedError):
        await booking_service.complete(own.booking_id, rule=write_rule)

    with system_context(fake_user_id=client.user_id):
        cancelled = await booking_service.cancel(own.booking_id, rule=cancel_rule)
    assert cancelled.status == BookingStatus.CANCELLED

    with pytest.raises(NotFoundError):
        await booking_service.cancel(env["booking_other"].booking_id, rule=cancel_rule)


async def test_groomer_sees_only_own_bookings_and_schedule(env):
    groomer = env["groomer"]
    booking_service = BookingService(env["uow_factory"])
    schedule_service = WorkScheduleService(env["uow_factory"])

    booking_read_rule = await _rule(
        Role.GROOMER,
        Permission.BOOK_READ,
        user_id=groomer.user_id,
        owner_field="master_id",
    )
    booking_write_rule = await _rule(
        Role.GROOMER,
        Permission.BOOK_WRITE,
        user_id=groomer.user_id,
        owner_field="master_id",
    )
    items = await booking_service.get_multi(rule=booking_read_rule)
    ids = {booking.booking_id for booking in items}
    assert env["booking_client"].booking_id in ids
    assert env["booking_for_groomer"].booking_id in ids
    assert env["booking_other"].booking_id not in ids
    assert await booking_service.get(env["booking_other"].booking_id, rule=booking_read_rule) is None

    schedule_rule = await _rule(
        Role.GROOMER,
        Permission.SCHEDULE_READ,
        user_id=groomer.user_id,
        owner_field="master_id",
    )
    assert await schedule_service.get(env["schedule"].work_schedule_id, rule=schedule_rule) is not None
    assert await schedule_service.get(env["schedule2"].work_schedule_id, rule=schedule_rule) is None

    with system_context(fake_user_id=groomer.user_id):
        completed = await booking_service.complete(
            env["booking_for_groomer"].booking_id, rule=booking_write_rule
        )
    assert completed.status == BookingStatus.COMPLETED

    with pytest.raises(NotFoundError):
        await booking_service.complete(env["booking_other"].booking_id, rule=booking_write_rule)

    start = datetime.combine(DAY, time(15, 0), tzinfo=get_default_tz())
    with pytest.raises(PermissionDeniedError):
        await booking_service.create(
            BookingCreate(
                master_id=env["groomer2"].user_id,
                service_id=env["service"].service_id,
                start_time=start,
                client_id=env["client2"].user_id,
            ),
            rule=booking_write_rule,
        )


async def test_manager_permissions_and_denials(env):
    manager = env["manager"]

    for permission in (
        Permission.SERVICE_WRITE,
        Permission.MASTER_WRITE,
        Permission.SCHEDULE_WRITE,
        Permission.DICTIONARIES_WRITE,
        Permission.STORAGE_WRITE,
    ):
        rule = await _rule(Role.MANAGER, permission, min_scope=Scope.ALL)
        assert rule.scope == Scope.ALL

    with pytest.raises(PermissionDeniedError):
        await _rule(Role.MANAGER, Permission.MASTER_DELETE, min_scope=Scope.ALL)
    with pytest.raises(PermissionDeniedError):
        await _rule(Role.MANAGER, Permission.USER_WRITE, min_scope=Scope.ALL)
    with pytest.raises(PermissionDeniedError):
        await require_role(Role.ADMIN)(manager)


async def test_admin_can_assign_role_and_mask_is_recalculated(env):
    admin = env["admin"]
    client = env["client"]
    user_service = UserService(env["uow_factory"])

    await require_role(Role.ADMIN)(admin)

    with system_context(fake_user_id=admin.user_id):
        updated = await user_service.update_role(client.user_id, Role.MANAGER)

    assert updated.role == Role.MANAGER
    assert updated.permission_mask == ROLE_MASK[Role.MANAGER]


async def test_service_token_is_limited_to_shared_endpoints(env):
    booking_service = BookingService(env["uow_factory"])

    service_booking_rule = await _rule(
        None, Permission.BOOK_READ, allow_service=True
    )
    assert service_booking_rule.scope == Scope.ALL
    all_bookings = await booking_service.get_multi(rule=service_booking_rule)
    assert len(all_bookings) >= 3

    with pytest.raises(PermissionDeniedError):
        await _rule(None, Permission.SERVICE_WRITE, allow_service=False)

    service_principal = Principal(kind=PrincipalKind.SERVICE)
    await require_service(service_principal)

    user_principal = Principal(
        kind=PrincipalKind.USER, user=_fake_user(Role.ADMIN, 1)
    )
    with pytest.raises(PermissionDeniedError):
        await require_service(user_principal)


async def test_dictionary_write_is_available_to_admin_and_manager(env):
    measure_service = MeasureUnitService(env["uow_factory"])
    rule = await _rule(Role.MANAGER, Permission.DICTIONARIES_WRITE, min_scope=Scope.ALL)

    with system_context(fake_user_id=env["manager"].user_id):
        created = await measure_service.create(
            MeasureUnitCreate(title=f"тест-{uuid.uuid4().hex[:6]}"), rule=rule
        )
    assert created.measure_unit_id is not None

    with pytest.raises(PermissionDeniedError):
        await _rule(Role.CLIENT, Permission.DICTIONARIES_WRITE, min_scope=Scope.ALL)
