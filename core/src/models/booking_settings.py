from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base_model import Base

# Значение по умолчанию, если настройка ещё не задана администратором.
DEFAULT_SLOT_INTERVAL_MINUTES = 30


class BookingSettings(Base):
    """Глобальные настройки системы бронирования.

    Таблица задумана как singleton: одна строка с
    ``booking_settings_id = 1``. Сейчас хранит только шаг сетки слотов
    (``slot_interval_minutes``), который настраивает администратор через
    ``POST /slots/interval``.

    Слоты при этом *не* хранятся в БД — они рассчитываются на лету из
    ``work_schedules``, длительности/буферов услуги и существующих броней.
    Здесь лежит только административно заданный шаг сетки.
    """

    __tablename__ = "booking_settings"

    booking_settings_id: Mapped[int] = mapped_column(primary_key=True)
    slot_interval_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=DEFAULT_SLOT_INTERVAL_MINUTES,
        server_default=str(DEFAULT_SLOT_INTERVAL_MINUTES),
    )
