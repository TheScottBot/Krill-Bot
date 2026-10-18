"""Pure server-board aggregation and streak calculations."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction


class BoardPeriod(StrEnum):
    """Supported rolling board periods."""

    WEEK = "week"
    MONTH = "month"
    ALL = "all"


@dataclass(frozen=True, slots=True)
class BoardEntry:
    """The minimal stored fields needed for board calculations."""

    user_id: int
    daily_number: int
    score: int


@dataclass(frozen=True, slots=True)
class BoardStanding:
    """One aggregated player row on a server board."""

    user_id: int
    dives: int
    total: int
    # Exact, because scores have no upper bound and float division overflows.
    average: Fraction
    best: int


@dataclass(frozen=True, slots=True)
class Streak:
    """Current and longest runs of consecutive daily numbers."""

    current: int
    longest: int


def compile_board(
    entries: tuple[BoardEntry, ...] | list[BoardEntry],
    period: BoardPeriod,
    *,
    current_daily_number: int,
) -> list[BoardStanding]:
    """Aggregate entries into a deterministic total-score ranking."""
    period_lengths = {
        BoardPeriod.WEEK: 7,
        BoardPeriod.MONTH: 30,
    }
    minimum_daily_number = (
        None if period is BoardPeriod.ALL else current_daily_number - period_lengths[period] + 1
    )
    scores_by_user: dict[int, list[int]] = {}
    for entry in entries:
        if minimum_daily_number is not None and entry.daily_number < minimum_daily_number:
            continue
        scores_by_user.setdefault(entry.user_id, []).append(entry.score)

    standings = [
        BoardStanding(
            user_id=user_id,
            dives=len(scores),
            total=sum(scores),
            average=Fraction(sum(scores), len(scores)),
            best=max(scores),
        )
        for user_id, scores in scores_by_user.items()
    ]
    return sorted(
        standings,
        key=lambda standing: (
            -standing.total,
            -standing.best,
            -standing.dives,
            standing.user_id,
        ),
    )


def calculate_streak(
    daily_numbers: tuple[int, ...] | list[int],
    *,
    current_daily_number: int,
) -> Streak:
    """Calculate current and longest streaks from distinct daily numbers."""
    ordered_numbers = sorted(set(daily_numbers))
    if not ordered_numbers:
        return Streak(current=0, longest=0)

    longest = 1
    consecutive = 1
    for previous_number, daily_number in zip(ordered_numbers, ordered_numbers[1:], strict=False):
        if daily_number == previous_number + 1:
            consecutive += 1
            longest = max(longest, consecutive)
        else:
            consecutive = 1

    current = consecutive if ordered_numbers[-1] == current_daily_number else 0
    return Streak(current=current, longest=longest)
