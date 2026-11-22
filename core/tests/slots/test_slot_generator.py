"""Юнит-тесты чистого генератора слотов (без БД).

Проверяют сетку по графику, буферы, пересечения и вспомогательные функции.
"""

from datetime import date, time, timedelta

from src.services.slot_generator import (
    generate_slot_times,
    intervals_overlap,
    iter_days,
    minutes_from_duration,
    slot_footprint,
)

DAY = date(2026, 11, 24)  # вторник


def test_full_day_grid_without_buffers():
    slots = generate_slot_times(DAY, time(9, 0), time(18, 0), 60)

    assert len(slots) == 9
    assert slots[0][0].strftime("%H:%M") == "09:00"
    assert slots[-1][1].strftime("%H:%M") == "18:00"


def test_grid_accounts_for_buffers():
    slots = generate_slot_times(DAY, time(9, 0), time(18, 0), 60, 10, 10)

    starts = [start.strftime("%H:%M") for start, _ in slots]
    assert starts == [
        "09:10", "10:30", "11:50", "13:10", "14:30", "15:50",
    ]


def test_custom_step_creates_dense_grid():
    slots = generate_slot_times(
        DAY, time(9, 0), time(11, 0), 60, step_minutes=30
    )

    assert len(slots) == 3  # 09:00, 09:30, 10:00


def test_day_too_short_returns_empty():
    assert generate_slot_times(DAY, time(9, 0), time(9, 30), 60) == []


def test_footprint_and_overlap():
    early = slot_footprint(
        *generate_slot_times(DAY, time(9, 0), time(18, 0), 60)[0], 10, 10
    )
    later = slot_footprint(
        *generate_slot_times(DAY, time(9, 0), time(18, 0), 60)[1], 10, 10
    )
    assert not intervals_overlap(early, later)

    slots = generate_slot_times(DAY, time(9, 0), time(18, 0), 60)
    with_after_buffer = slot_footprint(*slots[0], 0, 30)
    assert intervals_overlap(with_after_buffer, slots[1])


def test_iter_days_inclusive():
    assert len(iter_days(date(2026, 11, 24), date(2026, 11, 26))) == 3
    assert iter_days(date(2026, 11, 26), date(2026, 11, 24)) == []


def test_minutes_from_duration():
    assert minutes_from_duration(timedelta(hours=1, minutes=30)) == 90
    assert minutes_from_duration(None) is None
