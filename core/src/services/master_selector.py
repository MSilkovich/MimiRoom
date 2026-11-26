"""Стратегия выбора мастера, когда клиент его не указал.

Вынесено отдельной чистой функцией, чтобы логику можно было заменить, не
меняя расчёт слотов: ``SlotService`` просто вызывает
``select_master_for_day`` для каждого дня.

Текущая логика (можно переписать):
1. рассматриваем только мастеров, у которых в этот день есть свободные слоты;
2. предпочитаем мастера, у которого уже есть хотя бы одна запись в этот день
   (консолидация графика — меньше «рваных» окон);
3. среди них — у кого записей больше;
4. затем — у кого больше свободных слотов;
5. при равенстве — наименьший ``master_id`` (детерминизм).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class MasterDayAvailability:
    """Доступность одного мастера на конкретный день."""

    master_id: int
    free_slots: list[tuple[datetime, datetime]]
    bookings_that_day: int = 0


def select_master_for_day(
    options: list[MasterDayAvailability],
) -> int | None:
    """Выбрать ``master_id`` на день или ``None``, если свободных слотов нет."""

    candidates = [option for option in options if option.free_slots]
    if not candidates:
        return None

    def sort_key(option: MasterDayAvailability) -> tuple:
        has_bookings = option.bookings_that_day > 0
        return (
            0 if has_bookings else 1,          # сначала те, у кого есть записи
            -option.bookings_that_day,          # больше записей — выше
            -len(option.free_slots),            # больше свободы — выше
            option.master_id,                   # детерминированный тай-брейк
        )

    candidates.sort(key=sort_key)
    return candidates[0].master_id
