from datetime import date, datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload, selectinload

from ..context import get_current_user
from ..models import Breed, Pet, User
from ..models.booking import Booking
from ..models.enums.booking_status import BookingStatus
from ..models.master_service import MasterService as MasterServiceLink
from ..permissions.enums.roles import Role
from ..schemas import AppointmentSummary, PetSummary, Summary, UserSummary
from .sqlalchemy_repository import SqlAlchemyRepository


def _age_years(birthday: date | None) -> int | None:
    """Возраст в полных годах на сегодня (``None``, если дата неизвестна)."""
    if birthday is None:
        return None
    today = date.today()
    return today.year - birthday.year - (
        (today.month, today.day) < (birthday.month, birthday.day)
    )


class UserRepository(SqlAlchemyRepository[User]):
    def __init__(self, session):
        super().__init__(User, session)

    async def get_summary_by_id(self, user_id: int) -> Summary | None:
        # NOTE: только для использования в system_context - к текущему пользователю не обращаться, прав доступа нет
        stmt = (
            select(User)
            .where(User.user_id == user_id)
            .options(
                selectinload(User.pets)
                .joinedload(Pet.breed)
                .joinedload(Breed.pet_type)
            )
        )

        u = (await self.session.execute(stmt)).scalar_one_or_none()
        if not u:
            return None

        pets = [
            PetSummary(
                id=p.pet_id,
                name=p.name,
                pet_type_id=(p.breed.pet_type_id if p.breed else None),
                pet_type=(
                    p.breed.pet_type.title
                    if p.breed and p.breed.pet_type
                    else None
                ),
                breed_id=p.breed_id,
                breed=(p.breed.title if p.breed else None),
                birthday=p.birthday,
                age_years=_age_years(p.birthday),
            )
            for p in u.pets
        ]

        # Ближайшие активные записи клиента (для контекста модели).
        now = datetime.now(timezone.utc)
        bookings_stmt = (
            select(Booking)
            .where(
                Booking.client_id == user_id,
                Booking.is_deleted.is_(False),
                Booking.status.in_(
                    [BookingStatus.PENDING, BookingStatus.CONFIRMED]
                ),
                Booking.start_time >= now,
            )
            .order_by(Booking.start_time)
            .limit(5)
        )
        bookings = (
            (await self.session.execute(bookings_stmt))
            .scalars()
            .unique()
            .all()
        )
        appointments = [
            AppointmentSummary(
                booking_id=b.booking_id,
                service_id=b.service_id,
                service_title=(b.service.title if b.service else None),
                master_id=b.master_id,
                master_name=(
                    f"{b.master.name} {b.master.surname}".strip()
                    if b.master
                    else None
                ),
                start_time=b.start_time,
                end_time=b.end_time,
                status=(
                    b.status.value
                    if hasattr(b.status, "value")
                    else str(b.status)
                ),
            )
            for b in bookings
        ]

        return Summary(
            user=UserSummary(id=u.user_id, name=u.name, phone=u.phone),
            pets=pets,
            appointments=appointments,
        )

    # region мастера (users с ролью groomer)

    async def get_masters(
        self, limit: int = 100, offset: int = 0
    ) -> list[User]:
        return await self.get_multi(
            order="user_id",
            limit=limit,
            offset=offset,
            role=Role.GROOMER,
        )

    async def replace_master_services(
        self, master_id: int, service_ids: list[int]
    ) -> None:
        """Полностью переписать набор услуг мастера (many-to-many)."""
        await self.session.execute(
            delete(MasterServiceLink).where(
                MasterServiceLink.master_id == master_id
            )
        )
        user = get_current_user()
        user_id = user.user_id if user is not None else 0
        for service_id in dict.fromkeys(service_ids):
            self.session.add(
                MasterServiceLink(
                    master_id=master_id,
                    service_id=service_id,
                    who_create=user_id,
                    who_update=user_id,
                )
            )
        await self.session.flush()

    async def get_master_service_ids(self, master_id: int) -> set[int]:
        rows = await self.session.execute(
            select(MasterServiceLink.service_id).where(
                MasterServiceLink.master_id == master_id
            )
        )
        return set(rows.scalars().all())

    async def get_masters_by_service(self, service_id: int) -> list[User]:
        """Мастера (role=groomer), которые оказывают услугу."""
        stmt = (
            select(User)
            .join(
                MasterServiceLink,
                MasterServiceLink.master_id == User.user_id,
            )
            .where(
                MasterServiceLink.service_id == service_id,
                MasterServiceLink.is_deleted.is_(False),
                User.role == Role.GROOMER,
                User.is_deleted.is_(False),
            )
            .order_by(User.user_id)
        )
        rows = await self.session.execute(stmt)
        return list(rows.scalars().unique().all())

    # endregion
