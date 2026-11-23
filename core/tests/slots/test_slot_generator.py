"""Юнит-тесты чистого расчёта слотов (без БД).

Проверяют построение сетки по графику, буферы, пересечения, отсев занятых
интервалов и вспомогательные функции.
"""

from datetime import date, datetime, time, timedelta

from src.services.slot_generator import (
    compute_available_slots,
    generate_slot_times,
    get_default_tz,
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


def test_intervals_overlap_and_footprint():
    slots = generate_slot_times(DAY, time(9, 0), time(18, 0), 60)

    early, later = slots[0], slots[1]  # 09:00-10:00, 10:00-11:00
    # Без буферов соседние слоты не пересекаются.
    assert not intervals_overlap(
        slot_footprint(*early, 0, 0), slot_footprint(*later, 0, 0)
    )
    # Буфер после расширяет footprint раннего слота до соседнего.
    with_after_buffer = slot_footprint(*early, 0, 30)
    assert intervals_overlap(with_after_buffer, later)


def test_compute_available_excludes_busy_footprint():
    tz = get_default_tz()
    busy_start = datetime.combine(DAY, time(10, 0), tzinfo=tz)
    busy_end = datetime.combine(DAY, time(11, 0), tzinfo=tz)
    busy = [slot_footprint(busy_start, busy_end, 0, 0)]

    free = compute_available_slots(
        day=DAY,
        start_time=time(9, 0),
        end_time=time(12, 0),
        duration_minutes=60,
        step_minutes=30,
        busy_footprints=busy,
        tz=tz,
    )

    starts = [start.strftime("%H:%M") for start, _ in free]
    # Кандидаты 09:00, 09:30, 10:00, 10:30, 11:00; занятое окно 10:00-11:00
    # снимает 09:30/10:00/10:30.
    assert starts == ["09:00", "11:00"]


def test_iter_days_inclusive():
    assert len(iter_days(date(2026, 11, 24), date(2026, 11, 26))) == 3
    assert iter_days(date(2026, 11, 26), date(2026, 11, 24)) == []


def test_minutes_from_duration():
    assert minutes_from_duration(timedelta(hours=1, minutes=30)) == 90
    assert minutes_from_duration(None) is None
