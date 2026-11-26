"""Юнит-тесты стратегии выбора мастера (без БД)."""

from datetime import datetime, time, timedelta

from src.services.master_selector import (
    MasterDayAvailability,
    select_master_for_day,
)

SLOT = (datetime(2026, 11, 24, 9, 0), datetime(2026, 11, 24, 10, 0))


def test_returns_none_when_no_free_slots():
    options = [
        MasterDayAvailability(1, [], bookings_that_day=2),
        MasterDayAvailability(2, [], bookings_that_day=0),
    ]
    assert select_master_for_day(options) is None


def test_prefers_master_with_bookings_that_day():
    options = [
        MasterDayAvailability(1, [SLOT, SLOT], bookings_that_day=0),
        MasterDayAvailability(2, [SLOT], bookings_that_day=1),
    ]
    # Мастер 2 уже занят в этот день — консолидируем его график.
    assert select_master_for_day(options) == 2


def test_more_bookings_wins_among_busy_masters():
    options = [
        MasterDayAvailability(1, [SLOT], bookings_that_day=1),
        MasterDayAvailability(2, [SLOT], bookings_that_day=3),
    ]
    assert select_master_for_day(options) == 2


def test_tie_break_by_lowest_id():
    options = [
        MasterDayAvailability(5, [SLOT], bookings_that_day=1),
        MasterDayAvailability(3, [SLOT], bookings_that_day=1),
    ]
    assert select_master_for_day(options) == 3
