from ..excpetions.crud import NotFoundError
from ..models.booking import Booking
from ..models.enums.booking_status import BookingStatus
from ..models.pet import Pet
from ..schemas import PetCreate, PetHistoryRead, PetUpdate
from .base import BaseService


class PetService(BaseService[Pet, PetCreate, PetUpdate]):
    model = Pet

    async def get_history(
        self,
        pet_id: int,
        status: BookingStatus | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PetHistoryRead]:
        """Вернуть историю посещений питомца (брони, новые сверху)."""
        async with self.uow_factory() as uow:
            pet = await uow.repository(Pet).get_single(pet_id=pet_id)
            if pet is None:
                raise NotFoundError("Питомец не найден")

            bookings: list[Booking] = await uow.repository(Booking).get_for_pet(
                pet_id, status=status, limit=limit, offset=offset
            )

            return [
                PetHistoryRead(
                    booking_id=booking.booking_id,
                    service_id=booking.service_id,
                    service_title=(
                        booking.service.title if booking.service else None
                    ),
                    master_id=booking.master_id,
                    master_name=(
                        f"{booking.master.name} {booking.master.surname}".strip()
                        if booking.master
                        else None
                    ),
                    start_time=booking.start_time,
                    end_time=booking.end_time,
                    status=booking.status,
                )
                for booking in bookings
            ]
