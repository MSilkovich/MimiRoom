from enum import Enum


class BookingStatus(str, Enum):
    """Статус бронирования.

    Слоты больше не материализуются, поэтому отдельного статуса слота нет.
    ``cancelled`` — единственный статус, при котором время записи снова
    доступно для новых броней; ``completed`` — визит оказан и сохранён
    в истории питомца (интервал продолжает считаться занятым).
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
