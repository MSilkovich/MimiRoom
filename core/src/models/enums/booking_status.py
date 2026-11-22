from enum import Enum


class BookingStatus(str, Enum):
    """Статус бронирования.

    ``cancelled`` — единственный статус, при котором слот снова доступен;
    поэтому в БД по ``slot_id`` строится частичный уникальный индекс, который
    запрещает более одного *активного* бронирования на один слот.
    """

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
