"""Tests for the pure time-of-day grammar and daily occurrence arithmetic."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from krillbot.clock import (
    MAXIMUM_CLOCK_TEXT_LENGTH,
    next_occurrence,
    parse_clock,
    previous_occurrence,
)

LONDON = ZoneInfo("Europe/London")


@pytest.mark.parametrize(
    ("supplied_text", "expected_clock"),
    [
        ("17:00", "17:00"),
        ("5pm", "17:00"),
        ("4am", "04:00"),
        ("6:30pm", "18:30"),
        ("0930", "09:30"),
        ("9.15", "09:15"),
        (" 21:00 ", "21:00"),
        ("12am", "00:00"),
        ("12pm", "12:00"),
        ("5 PM", "17:00"),
    ],
)
def test_parse_clock_reads_common_ways_of_writing_a_time(
    supplied_text: str,
    expected_clock: str,
) -> None:
    assert parse_clock(supplied_text) == expected_clock


@pytest.mark.parametrize("supplied_text", ["25:00", "13pm", "0am", "17:60", "soon", "", "1:2"])
def test_parse_clock_refuses_text_that_is_not_a_time_of_day(supplied_text: str) -> None:
    assert parse_clock(supplied_text) is None


def test_parse_clock_refuses_over_long_text_before_matching() -> None:
    assert parse_clock(" " * MAXIMUM_CLOCK_TEXT_LENGTH + "5pm") is None


def test_next_occurrence_is_later_today_when_the_time_has_not_passed() -> None:
    assert next_occurrence("17:00", datetime(2026, 10, 18, 15, 0, tzinfo=UTC), LONDON) == (
        datetime(2026, 10, 18, 16, 0, tzinfo=UTC)
    )


def test_next_occurrence_is_tomorrow_once_the_time_is_reached() -> None:
    assert next_occurrence("17:00", datetime(2026, 10, 18, 16, 0, tzinfo=UTC), LONDON) == (
        datetime(2026, 10, 19, 16, 0, tzinfo=UTC)
    )


def test_next_occurrence_follows_the_local_clock_across_the_end_of_summer_time() -> None:
    assert next_occurrence("17:00", datetime(2026, 10, 24, 17, 0, tzinfo=UTC), LONDON) == (
        datetime(2026, 10, 25, 17, 0, tzinfo=UTC)
    )


def test_previous_occurrence_is_earlier_today_once_the_time_has_passed() -> None:
    assert previous_occurrence("04:00", datetime(2026, 10, 18, 16, 0, tzinfo=UTC), LONDON) == (
        datetime(2026, 10, 18, 3, 0, tzinfo=UTC)
    )


def test_previous_occurrence_is_yesterday_before_the_time_is_reached() -> None:
    assert previous_occurrence("04:00", datetime(2026, 10, 18, 2, 0, tzinfo=UTC), LONDON) == (
        datetime(2026, 10, 17, 3, 0, tzinfo=UTC)
    )


def test_previous_occurrence_includes_the_exact_instant() -> None:
    reset_instant = datetime(2026, 10, 18, 3, 0, tzinfo=UTC)

    assert previous_occurrence("04:00", reset_instant, LONDON) == reset_instant
