from ..context import get_current_user
from ..models.booking_settings import (
    DEFAULT_SLOT_INTERVAL_MINUTES,
    BookingSettings,
)
from .sqlalchemy_repository import SqlAlchemyRepository

SETTINGS_ROW_ID = 1


class BookingSettingsRepository(SqlAlchemyRepository[BookingSettings]):
    """Доступ к singleton-строке настроек бронирования."""

    def __init__(self, session):
        super().__init__(BookingSettings, session)

    async def get_interval(self) -> int:
        """Вернуть текущий шаг сетки слотов (минуты) или значение по умолчанию."""
        row = await self.get_single(booking_settings_id=SETTINGS_ROW_ID)
        if row is None:
            return DEFAULT_SLOT_INTERVAL_MINUTES
        return row.slot_interval_minutes

    async def set_interval(self, minutes: int) -> int:
        """Сохранить новый шаг сетки слотов и вернуть его.

        Строку создаём при необходимости (upsert), аудит заполняем от текущего
        пользователя, а вне запроса (например, в тестах) — от системного id.
        """
        user = get_current_user()
        user_id = user.user_id if user is not None else 0

        row = await self.get_single(booking_settings_id=SETTINGS_ROW_ID)
        if row is None:
            row = BookingSettings(
                booking_settings_id=SETTINGS_ROW_ID,
                slot_interval_minutes=minutes,
                who_create=user_id,
                who_update=user_id,
            )
            self.session.add(row)
        else:
            row.slot_interval_minutes = minutes
            row.who_update = user_id
        await self.session.flush()
        return minutes
