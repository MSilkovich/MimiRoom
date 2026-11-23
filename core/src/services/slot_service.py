"""Расчёт доступных слотов и административный интервал сетки.

Ключевая идея: **слоты не хранятся в БД**. Возможные слоты для новой записи
вычисляются на лету из:
- графика мастера (``work_schedules``),
- длительности и буферов услуги (``service``),
- административного шага сетки (``booking_settings.slot_interval_minutes``),
- уже существующих активных броней (их footprint'ов с буферами).

Если клиент не указал мастера, конкретного мастера выбирает функция
``select_master_for_day`` (см. ``master_selector.py``) — её легко заменить.
"""

from datetime import date, datetime, time, timedelta

from src.excpetions.crud import NotFoundError, ValidationError
from src.models.booking import Booking
from src.models.booking_settings import BookingSettings
from src.models.service import Service
from src.models.user import User
from src.models.work_schedule import WorkSchedule
from src.permissions.enums.roles import Role
from src.schemas import SlotRead, SlotsAvailableRequest
from .master_selector import MasterDayAvailability, select_master_for_day
from .slot_generator import (
    compute_available_slots,
    get_default_tz,
    iter_days,
    minutes_from_duration,
    slot_footprint,
)


def _ensure_aware(value: datetime, tz) -> datetime:
    """Привести datetime к aware-виду в ``tz``."""
    if value.tzinfo is None:
        return value.replace(tzinfo=tz)
    return value.astimezone(tz)


def _local_date(value: datetime, tz) -> date:
    """Дата брони в локальной таймзоне."""
    return _ensure_aware(value, tz).date()


class SlotService:
    """Сервис расчёта слотов и настроек интервала."""

    def __init__(self, uow_factory) -> None:
        self.uow_factory = uow_factory

    # region интервал сетки (административная настройка)

    async def get_interval(self) -> int:
        """Вернуть текущий шаг сетки слотов (минуты)."""
        async with self.uow_factory() as uow:
            repo = uow.repository(BookingSettings)
            return await repo.get_interval()

    async def set_interval(self, interval_minutes: int) -> int:
        """Задать шаг сетки слотов (только администратор — проверка в роутере)."""
        if interval_minutes <= 0:
            raise ValidationError("Интервал слотов должен быть > 0")
        async with self.uow_factory() as uow:
            repo = uow.repository(BookingSettings)
            value = await repo.set_interval(interval_minutes)
            await uow.commit()
            return value

    # endregion

    # region расчёт доступности

    async def list_available(
        self, data: SlotsAvailableRequest
    ) -> list[SlotRead]:
        """Рассчитать свободные слоты под услугу на период.

        ``master_id`` опционален: если не задан — подбираем мастера на каждый
        день через ``select_master_for_day`` и возвращаем его слоты.
        """
        date_to = data.date_to or data.date_from
        if date_to < data.date_from:
            raise ValidationError("date_to не может быть раньше date_from")

        tz = get_default_tz()

        async with self.uow_factory() as uow:
            service_repo = uow.repository(Service)
            user_repo = uow.repository(User)
            schedule_repo = uow.repository(WorkSchedule)
            booking_repo = uow.repository(Booking)
            settings_repo = uow.repository(BookingSettings)

            service = await service_repo.get_single(
                service_id=data.service_id
            )
            if service is None:
                raise NotFoundError("Услуга не найдена")

            duration = minutes_from_duration(service.duration)
            if duration is None or duration <= 0:
                raise ValidationError("У услуги не задана длительность")

            interval = await settings_repo.get_interval()

            masters = await self._resolve_masters(
                user_repo,
                service,
                data.master_id,
            )

            scheduler = {}
            busy: dict[int, list] = {}
            counts: dict[int, dict] = {}

            for master in masters:
                rows = await schedule_repo.get_for_master(master.user_id)
                scheduler[master.user_id] = {
                    row.weekday: row for row in rows if not row.is_deleted
                }

            range_start = datetime.combine(
                data.date_from, time.min, tzinfo=tz
            )
            range_end = datetime.combine(
                date_to + timedelta(days=1), time.min, tzinfo=tz
            )
            # Расширяем окно на сутки, чтобы поймать брони с буферами,
            # «залезающие» в окно из соседних дней.
            fetch_start = range_start - timedelta(days=1)
            fetch_end = range_end + timedelta(days=1)

            for master in masters:
                bookings = await booking_repo.get_active_for_master(
                    master.user_id, fetch_start, fetch_end
                )
                footprints = []
                day_counts: dict[date, int] = {}
                for booking in bookings:
                    booking_service = booking.service
                    if booking_service is None:
                        continue
                    footprints.append(
                        slot_footprint(
                            _ensure_aware(booking.start_time, tz),
                            _ensure_aware(booking.end_time, tz),
                            booking_service.buffer_before_minutes,
                            booking_service.buffer_after_minutes,
                        )
                    )
                    day = _local_date(booking.start_time, tz)
                    day_counts[day] = day_counts.get(day, 0) + 1
                busy[master.user_id] = footprints
                counts[master.user_id] = day_counts

            result: list[SlotRead] = []
            for day in iter_days(data.date_from, date_to):
                options: list[MasterDayAvailability] = []
                free_by_master: dict[int, list] = {}
                for master in masters:
                    schedule = scheduler[master.user_id].get(day.weekday())
                    if schedule is None or schedule.is_day_off:
                        free_slots = []
                    else:
                        free_slots = compute_available_slots(
                            day=day,
                            start_time=schedule.start_time,
                            end_time=schedule.end_time,
                            duration_minutes=duration,
                            buffer_before_minutes=service.buffer_before_minutes,
                            buffer_after_minutes=service.buffer_after_minutes,
                            step_minutes=interval,
                            busy_footprints=busy[master.user_id],
                            tz=tz,
                        )
                    free_by_master[master.user_id] = free_slots
                    options.append(
                        MasterDayAvailability(
                            master_id=master.user_id,
                            free_slots=free_slots,
                            bookings_that_day=counts[master.user_id].get(
                                day, 0
                            ),
                        )
                    )

                if data.master_id is not None:
                    chosen_masters = [masters[0].user_id]
                else:
                    chosen = select_master_for_day(options)
                    chosen_masters = [chosen] if chosen is not None else []

                for master_id in chosen_masters:
                    for start, end in free_by_master[master_id]:
                        result.append(
                            SlotRead(
                                master_id=master_id,
                                service_id=service.service_id,
                                start_time=start,
                                end_time=end,
                                available=True,
                            )
                        )

            return result

    async def _resolve_masters(
        self,
        user_repo,
        service: Service,
        master_id: int | None,
    ) -> list[User]:
        """Список мастеров для расчёта: явный или все, кто оказывает услугу."""
        if master_id is not None:
            master = await user_repo.get_single(user_id=master_id)
            if master is None:
                raise NotFoundError("Мастер не найден")
            if master.role != Role.GROOMER:
                raise ValidationError("Пользователь не является мастером")
            offered = await user_repo.get_master_service_ids(master.user_id)
            if service.service_id not in offered:
                raise ValidationError("Мастер не оказывает выбранную услугу")
            return [master]

        masters = await user_repo.get_masters_by_service(service.service_id)
        if not masters:
            raise ValidationError(
                "Для этой услуги не назначено ни одного мастера"
            )
        return masters

    # endregion
