"""Tests for pure board aggregation and streak calculations."""

from __future__ import annotations

from krillbot.boards import (
    BoardEntry,
    BoardPeriod,
    BoardStanding,
    Streak,
    calculate_streak,
    compile_board,
)

RESULTS = (
    BoardEntry(user_id=10, daily_number=100, score=100),
    BoardEntry(user_id=10, daily_number=99, score=300),
    BoardEntry(user_id=20, daily_number=100, score=250),
    BoardEntry(user_id=20, daily_number=95, score=200),
    BoardEntry(user_id=30, daily_number=71, score=700),
)


def test_week_board_uses_seven_daily_numbers_and_ranks_by_total() -> None:
    assert compile_board(RESULTS, BoardPeriod.WEEK, current_daily_number=100) == [
        BoardStanding(user_id=20, dives=2, total=450, average=225.0, best=250),
        BoardStanding(user_id=10, dives=2, total=400, average=200.0, best=300),
    ]


def test_month_board_uses_thirty_daily_numbers() -> None:
    standings = compile_board(RESULTS, BoardPeriod.MONTH, current_daily_number=100)

    assert [standing.user_id for standing in standings] == [30, 20, 10]


def test_all_time_board_has_no_daily_number_cutoff() -> None:
    standings = compile_board(RESULTS, BoardPeriod.ALL, current_daily_number=100)

    assert [(standing.user_id, standing.total) for standing in standings] == [
        (30, 700),
        (20, 450),
        (10, 400),
    ]


def test_board_ties_are_deterministic() -> None:
    tied_results = (
        BoardEntry(user_id=30, daily_number=100, score=200),
        BoardEntry(user_id=20, daily_number=100, score=200),
    )

    standings = compile_board(tied_results, BoardPeriod.WEEK, current_daily_number=100)

    assert [standing.user_id for standing in standings] == [20, 30]


def test_gap_breaks_current_and_longest_streaks() -> None:
    assert calculate_streak((94, 95, 97, 98, 99), current_daily_number=99) == Streak(
        current=3,
        longest=3,
    )


def test_current_streak_is_zero_when_latest_result_is_not_current() -> None:
    assert calculate_streak((94, 95, 96), current_daily_number=99) == Streak(
        current=0,
        longest=3,
    )


def test_duplicate_daily_numbers_do_not_inflate_a_streak() -> None:
    assert calculate_streak((98, 98, 99, 100), current_daily_number=100) == Streak(
        current=3,
        longest=3,
    )


def test_empty_history_has_zero_streaks() -> None:
    assert calculate_streak((), current_daily_number=100) == Streak(current=0, longest=0)


def test_board_average_is_exact_for_scores_beyond_float_range() -> None:
    enormous_score = int("9" * 400)
    entries = (
        BoardEntry(user_id=10, daily_number=100, score=enormous_score),
        BoardEntry(user_id=10, daily_number=99, score=enormous_score + 2),
    )

    standings = compile_board(entries, BoardPeriod.ALL, current_daily_number=100)

    assert standings[0].average == enormous_score + 1
