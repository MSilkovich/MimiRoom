from datetime import datetime, time, timedelta

from src.excpetions.crud import ConflictError, NotFoundError, ValidationError
from src.models.booking import Booking
from src.models.enums.booking_status import BookingStatus
from src.models.enums.slot_status import SlotStatus
from src.models.pet import Pet
from src.models.slot import Slot
from src.models.user import User
from src.schemas import BookingCreate, BookingUpdate
from .base import BaseService
from .slot_generator import get_default_tz, intervals_overlap, slot_footprint
from .slot_service import recalculate_slot_statuses


def _day_bounds(slot: Slot) -> tuple[datetime, datetime]:
    """Границы суток слота (в его таймзоне) — для пересчёта статусов."""
    tz = slot.start_time.tzinfo or get_default_tz()
    day_start = datetime.combine(slot.start_time.date(), time.min, tzinfo=tz)
    return day_start, day_start + timedelta(days=1)


class BookingService(BaseService[Booking, BookingCreate, BookingUpdate]):
    model = Booking

    @staticmethod
    def _client_snapshot(user: User) -> tuple[str, str | None]:
        full_name = f"{user.name} {user.surname}".strip()
        return full_name or user.login, user.phone

    async def create(self, data: BookingCreate) -> Booking:
        """Создать бронь с защитой от гонок.

        Транзакция:
        1. `advisory-lock` по мастеру — сериализует конкурентные запросы;
        2. `SELECT ... FOR UPDATE` по строке слота;
        3. проверка статуса и пересечений с активными бронями;
        4. вставка брони + перевод слота в ``booked`` + пересчёт соседей.
        """
        async with self.uow_factory() as uow:
            slot_repo = uow.repository(Slot)
            booking_repo = uow.repository(Booking)
            user_repo = uow.repository(User)
            pet_repo = uow.repository(Pet)

            slot = await slot_repo.get_single(slot_id=data.slot_id)
            if slot is None:
                raise NotFoundError("Слот не найден")

            # Блокировка на уровне мастера: даже брони на разные, но
            # пересекающиеся слоты одного мастера не пройдут одновременно.
            await booking_repo.acquire_master_lock(slot.master_id)

            # Перечитываем слот уже под блокировкой строки.
            slot = await slot_repo.get_for_update(data.slot_id)
            if slot is None:
                raise NotFoundError("Слот не найден")

            if slot.status in (SlotStatus.BOOKED, SlotStatus.BLOCKED):
                raise ConflictError("Слот недоступен для бронирования")

            service = slot.service
            if service is None:
                raise NotFoundError("Услуга слота не найдена")

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
            if not client_name or not client_phone:
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

            day_start, day_end = _day_bounds(slot)
            active_bookings = await booking_repo.get_active_for_master(
                slot.master_id, day_start, day_end
            )

            target_footprint = slot_footprint(
                slot.start_time,
                slot.end_time,
                service.buffer_before_minutes,
                service.buffer_after_minutes,
            )
            for active in active_bookings:
                if active.slot is None:
                    continue
                active_service = active.service or service
                active_footprint = slot_footprint(
                    active.slot.start_time,
                    active.slot.end_time,
                    active_service.buffer_before_minutes,
                    active_service.buffer_after_minutes,
                )
                if intervals_overlap(target_footprint, active_footprint):
                    raise ConflictError(
                        "Слот пересекается с существующим бронированием"
                    )

            booking = await booking_repo.create(
                {
                    "slot_id": slot.slot_id,
                    "service_id": slot.service_id,
                    "master_id": slot.master_id,
                    "client_id": data.client_id,
                    "pet_id": data.pet_id,
                    "client_name": client_name,
                    "client_phone": client_phone,
                    "comment": data.comment,
                    "options": data.options,
                    "status": BookingStatus.PENDING,
                }
            )
            await slot_repo.update(
                {"status": SlotStatus.BOOKED}, slot_id=slot.slot_id
            )
            await recalculate_slot_statuses(
                uow, slot.master_id, day_start, day_end
            )

            await uow.commit()
            reloaded = await booking_repo.get_single(
                booking_id=booking.booking_id
            )
            return reloaded or booking

    async def cancel(self, booking_id: int) -> Booking:
        """Отменить бронь и вернуть слот в ``free`` (идемпотентно)."""
        async with self.uow_factory() as uow:
            booking_repo = uow.repository(Booking)
            slot_repo = uow.repository(Slot)

            booking = await booking_repo.get_single(booking_id=booking_id)
            if booking is None:
                raise NotFoundError("Бронирование не найдено")
            if booking.status == BookingStatus.CANCELLED:
                return booking

            booking = await booking_repo.update(
                {"status": BookingStatus.CANCELLED}, booking_id=booking_id
            )
            slot = await slot_repo.get_single(slot_id=booking.slot_id)
            if slot is not None:
                day_start, day_end = _day_bounds(slot)
                await recalculate_slot_statuses(
                    uow, slot.master_id, day_start, day_end
                )

            await uow.commit()
            return await booking_repo.get_single(booking_id=booking_id)

    async def update(
        self, pk: int, data: BookingUpdate
    ) -> Booking | None:
        async with self.uow_factory() as uow:
            booking_repo = uow.repository(Booking)
            slot_repo = uow.repository(Slot)

            payload = data.model_dump(exclude_unset=True)
            if not payload:
                return await booking_repo.get_single(booking_id=pk)

            booking = await booking_repo.update(payload, booking_id=pk)

            if payload.get("status") == BookingStatus.CANCELLED:
                slot = await slot_repo.get_single(slot_id=booking.slot_id)
                if slot is not None:
                    day_start, day_end = _day_bounds(slot)
                    await recalculate_slot_statuses(
                        uow, slot.master_id, day_start, day_end
                    )

            await uow.commit()
            return await booking_repo.get_single(booking_id=pk)

    async def delete(self, pk: int, rule=None) -> None:
        """Мягко удалить бронь, предварительно освободив слот."""
        async with self.uow_factory() as uow:
            booking_repo = uow.repository(Booking)
            slot_repo = uow.repository(Slot)

            booking = await booking_repo.get_single(booking_id=pk)
            if booking is None:
                return
            if booking.status != BookingStatus.CANCELLED:
                booking = await booking_repo.update(
                    {"status": BookingStatus.CANCELLED}, booking_id=pk
                )
                slot = await slot_repo.get_single(slot_id=booking.slot_id)
                if slot is not None:
                    day_start, day_end = _day_bounds(slot)
                    await recalculate_slot_statuses(
                        uow, slot.master_id, day_start, day_end
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
