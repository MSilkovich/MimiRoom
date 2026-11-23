from datetime import datetime, time, timedelta

from src.excpetions.crud import ConflictError, NotFoundError, ValidationError
from src.models.booking import Booking
from src.models.booking_settings import BookingSettings
from src.models.enums.booking_status import BookingStatus
from src.models.pet import Pet
from src.models.service import Service
from src.models.user import User
from src.models.work_schedule import WorkSchedule
from src.permissions.enums.roles import Role
from src.schemas import BookingCreate, BookingUpdate
from .base import BaseService
from .slot_generator import (
    get_default_tz,
    intervals_overlap,
    minutes_from_duration,
    slot_footprint,
)


def _ensure_aware(value: datetime, tz) -> datetime:
    """Привести datetime к aware-виду в ``tz`` с точностью до секунды."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=tz)
    return value.astimezone(tz).replace(microsecond=0)


class BookingService(BaseService[Booking, BookingCreate, BookingUpdate]):
    """Создание и обслуживание броней по конкретному времени.

    Слоты не материализуются: в бронь пишется конкретный ``start_time``, а
    ``end_time`` вычисляется из длительности услуги. Пересечения (с учётом
    буферов услуг) проверяются под advisory-lock по мастеру.
    """

    model = Booking

    @staticmethod
    def _client_snapshot(user: User) -> tuple[str, str | None]:
        full_name = f"{user.name} {user.surname}".strip()
        return full_name or user.login, user.phone

    async def create(self, data: BookingCreate) -> Booking:
        """Создать бронь на конкретное время.

        Транзакция:
        1. валидация услуги/мастера/питомца и графика;
        2. `advisory-lock` по мастеру — сериализует конкурентные запросы;
        3. проверка пересечений (с учётом буферов) с активными бронями;
        4. вставка брони с конкретными ``start_time``/``end_time``.
        """
        tz = get_default_tz()
        start_time = _ensure_aware(data.start_time, tz)

        async with self.uow_factory() as uow:
            booking_repo = uow.repository(Booking)
            service_repo = uow.repository(Service)
            user_repo = uow.repository(User)
            pet_repo = uow.repository(Pet)
            schedule_repo = uow.repository(WorkSchedule)
            settings_repo = uow.repository(BookingSettings)

            service = await service_repo.get_single(
                service_id=data.service_id
            )
            if service is None:
                raise NotFoundError("Услуга не найдена")
            duration = minutes_from_duration(service.duration)
            if duration is None or duration <= 0:
                raise ValidationError("У услуги не задана длительность")

            master = await user_repo.get_single(user_id=data.master_id)
            if master is None:
                raise NotFoundError("Мастер не найден")
            if master.role != Role.GROOMER:
                raise ValidationError("Пользователь не является мастером")
            offered = await user_repo.get_master_service_ids(master.user_id)
            if service.service_id not in offered:
                raise ValidationError("Мастер не оказывает выбранную услугу")

            # --- график и сетка -------------------------------------------
            day = start_time.date()
            schedules = await schedule_repo.get_for_master(master.user_id)
            schedule = next(
                (
                    row
                    for row in schedules
                    if row.weekday == day.weekday() and not row.is_deleted
                ),
                None,
            )
            if schedule is None or schedule.is_day_off:
                raise ValidationError("В этот день мастер не работает")

            end_time = start_time + timedelta(minutes=duration)
            footprint = slot_footprint(
                start_time,
                end_time,
                service.buffer_before_minutes,
                service.buffer_after_minutes,
            )
            window_start = datetime.combine(
                day, schedule.start_time, tzinfo=tz
            )
            window_end = datetime.combine(day, schedule.end_time, tzinfo=tz)
            if footprint[0] < window_start or footprint[1] > window_end:
                raise ValidationError(
                    "Время записи вне графика работы мастера")

            interval = await settings_repo.get_interval()
            self._validate_grid(
                start_time, window_start, service, interval
            )

            # --- клиент: авторизованный или гость -------------------------
            client_name = data.client_name
            client_phone = data.client_phone
            if data.client_id is not None:
                client = await user_repo.get_single(user_id=data.client_id)
                if client is None:
                    raise NotFoundError("Клиент не найден")
                snapshot_name, snapshot_phone = self._client_snapshot(client)
                client_name = client_name or snapshot_name
                client_phone = client_phone or snapshot_phone
            elif not client_name or not client_phone:
                # Контакт обязателен только для гостя. Авторизованному клиенту
                # (client_id) телефон не нужен — НО он может отсутствовать в профиле.
                raise ValidationError(
                    "Укажите client_id или client_name и client_phone"
                )

            # --- питомец ---------------------------------------------------
            if data.pet_id is not None:
                pet = await pet_repo.get_single(pet_id=data.pet_id)
                if pet is None:
                    raise NotFoundError("Питомец не найден")
                if (
                    data.client_id is not None
                    and pet.owner_id is not None
                    and pet.owner_id != data.client_id
                ):
                    raise ValidationError(
                        "Питомец не принадлежит указанному клиенту"
                    )

            # --- блокировка и проверка пересечений ------------------------
            await booking_repo.acquire_master_lock(master.user_id)

            day_start = window_start
            day_end = datetime.combine(
                day + timedelta(days=1), time.min, tzinfo=tz
            )
            active_bookings = await booking_repo.get_active_for_master(
                master.user_id, day_start, day_end
            )
            for active in active_bookings:
                if active.service is None:
                    continue
                active_footprint = slot_footprint(
                    _ensure_aware(active.start_time, tz),
                    _ensure_aware(active.end_time, tz),
                    active.service.buffer_before_minutes,
                    active.service.buffer_after_minutes,
                )
                if intervals_overlap(footprint, active_footprint):
                    raise ConflictError(
                        "Время пересекается с существующим бронированием"
                    )

            booking = await booking_repo.create(
                {
                    "service_id": service.service_id,
                    "master_id": master.user_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "client_id": data.client_id,
                    "pet_id": data.pet_id,
                    "client_name": client_name,
                    "client_phone": client_phone,
                    "comment": data.comment,
                    "options": data.options,
                    "status": BookingStatus.PENDING,
                }
            )
            await uow.commit()
            reloaded = await booking_repo.get_single(
                booking_id=booking.booking_id
            )
            return reloaded or booking

    @staticmethod
    def _validate_grid(
        start_time: datetime,
        window_start: datetime,
        service: Service,
        interval: int | None,
    ) -> None:
        """Проверить, что время попадает в административную сетку слотов."""
        if not interval or interval <= 0:
            return
        grid_origin = window_start + timedelta(
            minutes=service.buffer_before_minutes
        )
        delta_minutes = int(
            round((start_time - grid_origin).total_seconds() / 60)
        )
        if delta_minutes < 0 or delta_minutes % interval != 0:
            raise ValidationError(
                "Время не соответствует сетке слотов (интервал "
                f"{interval} мин)"
            )

    async def cancel(self, booking_id: int) -> Booking:
        """Отменить бронь (идемпотентно)."""
        async with self.uow_factory() as uow:
            booking_repo = uow.repository(Booking)

            booking = await booking_repo.get_single(booking_id=booking_id)
            if booking is None:
                raise NotFoundError("Бронирование не найдено")
            if booking.status == BookingStatus.CANCELLED:
                return booking

            await booking_repo.update(
                {"status": BookingStatus.CANCELLED}, booking_id=booking_id
            )
            await uow.commit()
            return await booking_repo.get_single(booking_id=booking_id)

    async def update(
        self, pk: int, data: BookingUpdate
    ) -> Booking | None:
        async with self.uow_factory() as uow:
            booking_repo = uow.repository(Booking)

            payload = data.model_dump(exclude_unset=True)
            if not payload:
                return await booking_repo.get_single(booking_id=pk)

            await booking_repo.update(payload, booking_id=pk)
            await uow.commit()
            return await booking_repo.get_single(booking_id=pk)

    async def delete(self, pk: int, rule=None) -> None:
        """Мягко удалить бронь (активную — предварительно отменив)."""
        async with self.uow_factory() as uow:
            booking_repo = uow.repository(Booking)

            booking = await booking_repo.get_single(booking_id=pk)
            if booking is None:
                return
            if booking.status != BookingStatus.CANCELLED:
                await booking_repo.update(
                    {"status": BookingStatus.CANCELLED}, booking_id=pk
                )
            await booking_repo.delete(booking_id=pk)
            await uow.commit()

    async def get_multi(
        self,
        order: str | None = None,
        limit: int = 100,
        offset: int = 0,
        rule=None,
        master_id: int | None = None,
        client_id: int | None = None,
        status: BookingStatus | None = None,
    ) -> list[Booking]:
        filters: dict = {}
        if master_id is not None:
            filters["master_id"] = master_id
        if client_id is not None:
            filters["client_id"] = client_id
        if status is not None:
            filters["status"] = status
        async with self.uow_factory() as uow:
            repo = uow.repository(Booking)
            return await repo.get_multi(
                order=order, limit=limit, offset=offset, **filters
            )
