"""Pure grammar and score interpretation for known Krillion daily results."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

MAXIMUM_INPUT_LENGTH = 2_000

ROUND_POINTS = {
    "⬛": 0,
    "🫧": 10,
    "🐟": 30,
    "🦑": 60,
    "🏮": 85,
}


@dataclass(frozen=True, slots=True)
class Bearing:
    """A named total-score band published by Krillion."""

    minimum_score: int
    name: str
    description: str


BEARINGS = (
    Bearing(450, "One in a krillion", "Trench dweller. Absurd."),
    Bearing(351, "Deep cut", "Seriously deep dive."),
    Bearing(251, "Rare", "Below the thermocline. Nice."),
    Bearing(151, "Schooler", "Swimming with the school."),
    Bearing(0, "Plankton", "Plenty of ocean left down there."),
)


class ParseRejection(StrEnum):
    """A stable reason why supplied text was not accepted."""

    TOO_LONG = "too-long"
    NOT_A_RESULT = "not-a-result"
    SEVERAL_RESULTS = "several-results"


@dataclass(frozen=True, slots=True)
class ParsedResult:
    """The fields permitted to leave a matched daily-result block."""

    daily_number: int
    score: int
    emoji_row: str
    known_points_total: int
    row_fully_known: bool
    score_matches_known_points: bool


_DAILY_RESULT_PATTERN = re.compile(
    r"^Krillion #(?P<daily_number>[1-9][0-9]*) 🦐\r?\n"
    r"(?P<score>0|[1-9][0-9]*)\r?\n\r?\n"
    r"(?P<emoji_row>\S+)$",
    re.MULTILINE,
)


def bearing_for_score(score: int) -> Bearing:
    """Return the published bearing containing a non-negative score."""
    if score < 0:
        raise ValueError("score must not be negative")
    for bearing in BEARINGS:
        if score >= bearing.minimum_score:
            return bearing
    raise AssertionError("bearing table does not cover zero")


def parse_daily_result(supplied_text: str) -> ParsedResult | ParseRejection:
    """Find exactly one known daily-result block in untrusted message text."""
    if len(supplied_text) > MAXIMUM_INPUT_LENGTH:
        return ParseRejection.TOO_LONG

    parsed_results: list[ParsedResult] = []
    for matched_block in _DAILY_RESULT_PATTERN.finditer(supplied_text):
        emoji_row = matched_block.group("emoji_row")
        row_fully_known = all(symbol in ROUND_POINTS for symbol in emoji_row)
        if row_fully_known and len(emoji_row) != 7:
            continue
        score = int(matched_block.group("score"))
        known_points_total = sum(ROUND_POINTS.get(symbol, 0) for symbol in emoji_row)
        parsed_results.append(
            ParsedResult(
                daily_number=int(matched_block.group("daily_number")),
                score=score,
                emoji_row=emoji_row,
                known_points_total=known_points_total,
                row_fully_known=row_fully_known,
                score_matches_known_points=row_fully_known and score == known_points_total,
            )
        )

    if not parsed_results:
        return ParseRejection.NOT_A_RESULT
    if len(parsed_results) > 1:
        return ParseRejection.SEVERAL_RESULTS
    return parsed_results[0]
