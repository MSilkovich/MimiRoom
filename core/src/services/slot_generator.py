"""Генерация сетки слотов.

Модуль намеренно не зависит от БД и SQLAlchemy — это чистые функции, которые
легко тестировать. Слой сервисов (``SlotService``) использует их, чтобы
построить конкретные строки ``slots`` по графику мастера.

Соглашения:
- ``weekday`` — как в ``datetime.date.weekday()``: 0 = понедельник, 6 = воскресенье;
- ``slot.start_time`` / ``slot.end_time`` — интервал *самой услуги*;
- буферы до/после расширяют «фактический» интервал (footprint), который
  участвует в проверке пересечений, но не выдаётся клиенту как время записи.
"""

from __future__ import annotations

import os
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Europe/Moscow"

Interval = tuple[datetime, datetime]


@lru_cache(maxsize=1)
def get_default_tz() -> ZoneInfo:
    """Часовой пояс по умолчанию (переопределяется ``BOOKING_TZ``)."""
    return ZoneInfo(os.getenv("BOOKING_TZ", DEFAULT_TIMEZONE))


def minutes_from_duration(duration: timedelta | None) -> int | None:
    """Перевести ``timedelta`` в целое число минут."""
    if duration is None:
        return None
    return int(duration.total_seconds() // 60)


def slot_footprint(
    start: datetime,
    end: datetime,
    buffer_before_minutes: int = 0,
    buffer_after_minutes: int = 0,
) -> Interval:
    """Фактический интервал слота с учётом буферов до/после."""
    return (
        start - timedelta(minutes=max(buffer_before_minutes, 0)),
        end + timedelta(minutes=max(buffer_after_minutes, 0)),
    )


def intervals_overlap(a: Interval, b: Interval) -> bool:
    """Пересекаются ли два полуинтервала ``[start, end)``."""
    return a[0] < b[1] and b[0] < a[1]


def generate_slot_times(
    day: date,
    start_time: time,
    end_time: time,
    duration_minutes: int,
    buffer_before_minutes: int = 0,
    buffer_after_minutes: int = 0,
    step_minutes: int | None = None,
    tz: ZoneInfo | None = None,
) -> list[Interval]:
    """Построить сетку слотов на один день.

    Args:
        day: календарный день.
        start_time: начало рабочего дня мастера.
        end_time: конец рабочего дня мастера.
        duration_minutes: длительность услуги (минуты, > 0).
        buffer_before_minutes: подготовка до услуги.
        buffer_after_minutes: уборка/перерыв после услуги.
        step_minutes: шаг сетки. По умолчанию равен
            ``duration + buffer_before + buffer_after`` (слоты встык).
        tz: часовой пояс; по умолчанию ``BOOKING_TZ`` / Europe/Moscow.

    Returns:
        Список пар ``(start_time, end_time)`` услуги, timezone-aware.
        Пустой список, если день не помещается в рабочее окно.
    """
    if duration_minutes <= 0:
        raise ValueError("duration_minutes должен быть > 0")
    if buffer_before_minutes < 0 or buffer_after_minutes < 0:
        raise ValueError("буферы не могут быть отрицательными")

    tz = tz or get_default_tz()
    day_start = datetime.combine(day, start_time, tzinfo=tz)
    day_end = datetime.combine(day, end_time, tzinfo=tz)
    if day_end <= day_start:
        return []

    step = step_minutes or (
        duration_minutes + buffer_before_minutes + buffer_after_minutes
    )
    if step <= 0:
        raise ValueError("step_minutes должен быть > 0")

    duration = timedelta(minutes=duration_minutes)
    before = timedelta(minutes=buffer_before_minutes)
    after = timedelta(minutes=buffer_after_minutes)
    step_delta = timedelta(minutes=step)

    result: list[Interval] = []
    service_start = day_start + before
    service_end = service_start + duration
    footprint_start = service_start - before
    footprint_end = service_end + after

    # Защита от бесконечного цикла при очень маленьком step.
    max_iterations = 24 * 60 + 1
    while footprint_end <= day_end and footprint_start >= day_start:
        result.append((service_start, service_end))
        service_start += step_delta
        service_end = service_start + duration
        footprint_start = service_start - before
        footprint_end = service_end + after
        if len(result) > max_iterations:
            raise RuntimeError("Слишком много слотов за день")
    return result


def iter_days(date_from: date, date_to: date) -> list[date]:
    """Включительный список дней ``[date_from, date_to]``."""
    if date_to < date_from:
        return []
    days: list[date] = []
    current = date_from
    while current <= date_to:
        days.append(current)
        current += timedelta(days=1)
    return days
