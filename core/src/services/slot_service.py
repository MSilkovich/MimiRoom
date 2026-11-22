from datetime import date, datetime, time, timedelta

from src.excpetions.crud import NotFoundError, ValidationError
from src.models.booking import Booking
from src.models.enums.slot_status import SlotStatus
from src.models.resource import Resource
from src.models.service import Service
from src.models.slot import Slot
from src.models.work_schedule import WorkSchedule
from src.schemas import SlotGenerateRequest, SlotRead
from .base import BaseService
from .slot_generator import (
    generate_slot_times,
    get_default_tz,
    intervals_overlap,
    iter_days,
    minutes_from_duration,
    slot_footprint,
)


def _normalize_dt(value: datetime, tz) -> datetime:
    """Привести datetime к aware-виду в ``tz`` с точностью до секунды.

    Нужно для устойчивого сравнения «уже сгенерированных» start_time: разные
    драйверы могут вернуть naive (SQLite) или aware в другой зоне (Postgres).
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=tz)
    return value.astimezone(tz).replace(microsecond=0)


async def recalculate_slot_statuses(
    uow, resource_id: int, day_start: datetime, day_end: datetime
) -> None:
    """Пересчитать статусы слотов мастера за окно ``[day_start, day_end)``.

    Статус слота выводится из активных броней:
    - слот, на который есть активная бронь -> ``booked``;
    - слот, чей интервал с буферами пересекается с активной бронью -> ``blocked``;
    - иначе -> ``free``.

    Так один и тот же пересчёт закрывает и освобождение слота при отмене, и
    блокировку соседних слотов из-за буферов.
    """
    slot_repo = uow.repository(Slot)
    booking_repo = uow.repository(Booking)
    service_repo = uow.repository(Service)

    slots = await slot_repo.list_range(resource_id, day_start, day_end)
    if not slots:
        return

    services = await service_repo.get_many_by_ids(
        {slot.service_id for slot in slots}
    )
    service_map = {service.service_id: service for service in services}

    active_bookings = await booking_repo.get_active_for_resource(
        resource_id, day_start, day_end
    )
    booked_slot_ids = {booking.slot_id for booking in active_bookings}

    booked_footprints = []
    for booking in active_bookings:
        if booking.slot is None:
            continue
        service = service_map.get(booking.service_id) or booking.service
        if service is None:
            continue
        booked_footprints.append(
            slot_footprint(
                booking.slot.start_time,
                booking.slot.end_time,
                service.buffer_before_minutes,
                service.buffer_after_minutes,
            )
        )

    for slot in slots:
        if slot.slot_id in booked_slot_ids:
            new_status = SlotStatus.BOOKED
        else:
            service = service_map.get(slot.service_id)
            footprint = (
                slot_footprint(
                    slot.start_time,
                    slot.end_time,
                    service.buffer_before_minutes,
                    service.buffer_after_minutes,
                )
                if service is not None
                else (slot.start_time, slot.end_time)
            )
            overlaps = any(
                intervals_overlap(footprint, booked_footprint)
                for booked_footprint in booked_footprints
            )
            new_status = SlotStatus.BLOCKED if overlaps else SlotStatus.FREE

        if slot.status != new_status:
            await slot_repo.update(
                {"status": new_status}, slot_id=slot.slot_id
            )


class SlotService(BaseService[Slot, SlotRead, SlotRead]):
    model = Slot

    async def generate(
        self, data: SlotGenerateRequest
    ) -> tuple[int, list[Slot]]:
        """Идемпотентно сгенерировать слоты по графику мастера и услуге."""
        if data.date_to < data.date_from:
            raise ValidationError("date_to не может быть раньше date_from")

        async with self.uow_factory() as uow:
            resource_repo = uow.repository(Resource)
            service_repo = uow.repository(Service)
            schedule_repo = uow.repository(WorkSchedule)
            slot_repo = uow.repository(Slot)

            resource = await resource_repo.get_single(
                resource_id=data.resource_id
            )
            if resource is None:
                raise NotFoundError("Мастер не найден")
            if not resource.is_active:
                raise ValidationError("Мастер неактивен")

            service = await service_repo.get_single(service_id=data.service_id)
            if service is None:
                raise NotFoundError("Услуга не найдена")
            if not service.is_active:
                raise ValidationError("Услуга неактивна")

            offered_service_ids = await resource_repo.get_service_ids(
                data.resource_id
            )
            if data.service_id not in offered_service_ids:
                raise ValidationError("Мастер не оказывает выбранную услугу")

            duration = minutes_from_duration(service.duration)
            if duration is None or duration <= 0:
                raise ValidationError("У услуги не задана длительность")

            schedules = await schedule_repo.get_for_resource(data.resource_id)
            by_weekday = {
                schedule.weekday: schedule
                for schedule in schedules
                if not schedule.is_deleted
            }

            tz = get_default_tz()
            created = 0
            created_slots: list[Slot] = []

            for day in iter_days(data.date_from, data.date_to):
                schedule = by_weekday.get(day.weekday())
                if schedule is None or schedule.is_day_off:
                    continue

                day_start = datetime.combine(day, time.min, tzinfo=tz)
                day_end = datetime.combine(
                    day + timedelta(days=1), time.min, tzinfo=tz
                )

                existing = await slot_repo.existing_start_times(
                    data.resource_id, data.service_id, day_start, day_end
                )
                existing_normalized = {
                    _normalize_dt(value, tz) for value in existing
                }
                candidates = generate_slot_times(
                    day=day,
                    start_time=schedule.start_time,
                    end_time=schedule.end_time,
                    duration_minutes=duration,
                    buffer_before_minutes=service.buffer_before_minutes,
                    buffer_after_minutes=service.buffer_after_minutes,
                    step_minutes=data.step_minutes,
                    tz=tz,
                )

                items = [
                    {
                        "resource_id": data.resource_id,
                        "service_id": data.service_id,
                        "start_time": start,
                        "end_time": end,
                        "status": SlotStatus.FREE,
                    }
                    for start, end in candidates
                    if _normalize_dt(start, tz) not in existing_normalized
                ]
                if not items:
                    continue

                instances = await slot_repo.create_many(items)
                created += len(instances)
                created_slots.extend(instances)

            await uow.commit()
            return created, created_slots

    async def list_availability(
        self,
        resource_id: int,
        service_id: int,
        date_from: date,
        date_to: date,
        step_minutes: int | None = None,
        only_available: bool = False,
        limit: int = 500,
        offset: int = 0,
    ) -> list[Slot]:
        """Вернуть слоты с признаком доступности (пересчитанным по броням)."""
        await self.generate(
            SlotGenerateRequest(
                resource_id=resource_id,
                service_id=service_id,
                date_from=date_from,
                date_to=date_to,
                step_minutes=step_minutes,
            )
        )

        tz = get_default_tz()
        start = datetime.combine(date_from, time.min, tzinfo=tz)
        end = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=tz)

        async with self.uow_factory() as uow:
            await recalculate_slot_statuses(uow, resource_id, start, end)
            await uow.commit()

        async with self.uow_factory() as uow:
            slot_repo = uow.repository(Slot)
            slots = await slot_repo.list_range(
                resource_id, start, end, service_id=service_id
            )

        for slot in slots:
            slot.available = slot.status == SlotStatus.FREE

        if only_available:
            slots = [slot for slot in slots if slot.available]

        return slots[offset: offset + limit]

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        rule=None,
        resource_id: int | None = None,
        service_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: SlotStatus | None = None,
    ) -> list[Slot]:
        tz = get_default_tz()
        start = (
            datetime.combine(date_from, time.min, tzinfo=tz)
            if date_from is not None
            else None
        )
        end = (
            datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=tz)
            if date_to is not None
            else None
        )
        async with self.uow_factory() as uow:
            repo = uow.repository(Slot)
            return await repo.list_filtered(
                resource_id=resource_id,
                service_id=service_id,
                start=start,
                end=end,
                status=status,
                limit=limit,
                offset=offset,
            )
