"""Contract tests for the pure Krillion daily-result grammar."""

from __future__ import annotations

from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as strategies

from krillbot.result_grammar import (
    MAXIMUM_INPUT_LENGTH,
    ParsedResult,
    ParseRejection,
    bearing_for_score,
    parse_daily_result,
)

SAMPLE_DIRECTORY = Path(__file__).parent / "samples"
SAMPLE_EXPECTATIONS = (
    ("daily-95-435.txt", 95, 435, "🐟🏮🏮🦑🐟🏮🦑"),
    ("daily-94-235.txt", 94, 235, "🦑🐟🫧🐟🫧🫧🏮"),
    ("daily-94-150.txt", 94, 150, "🦑🫧⬛🫧🫧🐟🐟"),
    ("daily-94-335.txt", 94, 335, "🦑🦑🐟🐟🏮🫧🦑"),
    ("daily-93-225.txt", 93, 225, "🫧🦑🏮🫧🐟⬛🐟"),
    ("daily-93-235.txt", 93, 235, "🏮🫧🐟🫧🐟🫧🦑"),
)


@pytest.mark.parametrize(
    ("sample_name", "expected_daily_number", "expected_score", "expected_emoji_row"),
    SAMPLE_EXPECTATIONS,
)
def test_real_daily_samples_parse(
    sample_name: str,
    expected_daily_number: int,
    expected_score: int,
    expected_emoji_row: str,
) -> None:
    supplied_text = (SAMPLE_DIRECTORY / sample_name).read_text(encoding="utf-8")

    assert parse_daily_result(supplied_text) == ParsedResult(
        daily_number=expected_daily_number,
        score=expected_score,
        emoji_row=expected_emoji_row,
        known_points_total=expected_score,
        row_fully_known=True,
        score_matches_known_points=True,
    )


def test_result_is_found_inside_surrounding_conversation() -> None:
    supplied_text = (
        "conversation before\nKrillion #95 🦐\n435\n\n🐟🏮🏮🦑🐟🏮🦑\nconversation after"
    )

    assert parse_daily_result(supplied_text) == ParsedResult(
        daily_number=95,
        score=435,
        emoji_row="🐟🏮🏮🦑🐟🏮🦑",
        known_points_total=435,
        row_fully_known=True,
        score_matches_known_points=True,
    )


def test_score_mismatch_is_reported_without_rejecting_the_result() -> None:
    supplied_text = "Krillion #95 🦐\n436\n\n🐟🏮🏮🦑🐟🏮🦑"

    assert parse_daily_result(supplied_text) == ParsedResult(
        daily_number=95,
        score=436,
        emoji_row="🐟🏮🏮🦑🐟🏮🦑",
        known_points_total=435,
        row_fully_known=True,
        score_matches_known_points=False,
    )


def test_unknown_emoji_is_preserved_and_known_points_are_still_totalled() -> None:
    supplied_text = "Krillion #96 🦐\n435\n\n🐟🏮🏮🦑🐟🏮🧑‍🚀"

    assert parse_daily_result(supplied_text) == ParsedResult(
        daily_number=96,
        score=435,
        emoji_row="🐟🏮🏮🦑🐟🏮🧑‍🚀",
        known_points_total=375,
        row_fully_known=False,
        score_matches_known_points=False,
    )


@pytest.mark.parametrize(
    ("score", "expected_name", "expected_description"),
    (
        (0, "Plankton", "Plenty of ocean left down there."),
        (150, "Plankton", "Plenty of ocean left down there."),
        (151, "Schooler", "Swimming with the school."),
        (250, "Schooler", "Swimming with the school."),
        (251, "Rare", "Below the thermocline. Nice."),
        (350, "Rare", "Below the thermocline. Nice."),
        (351, "Deep cut", "Seriously deep dive."),
        (449, "Deep cut", "Seriously deep dive."),
        (450, "One in a krillion", "Trench dweller. Absurd."),
    ),
)
def test_bearing_boundaries(
    score: int,
    expected_name: str,
    expected_description: str,
) -> None:
    bearing = bearing_for_score(score)

    assert bearing.name == expected_name
    assert bearing.description == expected_description


def test_input_over_discord_message_limit_is_rejected_before_parsing() -> None:
    supplied_text = "x" * (MAXIMUM_INPUT_LENGTH + 1) + "\nKrillion #95 🦐\n435\n\n🐟🏮🏮🦑🐟🏮🦑"

    assert parse_daily_result(supplied_text) == ParseRejection.TOO_LONG


@pytest.mark.parametrize(
    "supplied_text",
    (
        "ordinary conversation",
        "Krillion #95 🦐\n435\n🐟🏮🏮🦑🐟🏮🦑",
        "Krillion #95 🦐\n435\n\n🐟🏮🏮🦑🐟🏮",
        "Krillion #95 🦐\n435\n\n🐟🏮🏮 🦑🐟🏮",
    ),
)
def test_malformed_or_unknown_daily_result_is_rejected(supplied_text: str) -> None:
    assert parse_daily_result(supplied_text) == ParseRejection.NOT_A_RESULT


def test_more_than_one_result_is_rejected() -> None:
    first_result = (SAMPLE_DIRECTORY / "daily-95-435.txt").read_text(encoding="utf-8")
    second_result = (SAMPLE_DIRECTORY / "daily-94-235.txt").read_text(encoding="utf-8")

    assert parse_daily_result(f"{first_result}\n{second_result}") == ParseRejection.SEVERAL_RESULTS


@settings(max_examples=150, deadline=None)
@given(strategies.text(max_size=2100))
def test_parser_never_raises_for_arbitrary_text(supplied_text: str) -> None:
    parse_daily_result(supplied_text)


@settings(max_examples=50, deadline=None)
@given(strategies.text(min_size=MAXIMUM_INPUT_LENGTH + 1, max_size=2100))
def test_parser_never_accepts_input_over_limit(supplied_text: str) -> None:
    assert parse_daily_result(supplied_text) == ParseRejection.TOO_LONG


@settings(max_examples=75, deadline=None)
@given(strategies.text(alphabet="abcdefghijklmnopqrstuvwxyz ", max_size=80))
def test_parser_returns_only_fields_from_the_result_block(surrounding_text: str) -> None:
    supplied_text = (
        f"{surrounding_text}\nKrillion #95 🦐\n435\n\n🐟🏮🏮🦑🐟🏮🦑\n{surrounding_text}"
    )

    parsed_result = parse_daily_result(supplied_text)

    assert parsed_result == ParsedResult(
        daily_number=95,
        score=435,
        emoji_row="🐟🏮🏮🦑🐟🏮🦑",
        known_points_total=435,
        row_fully_known=True,
        score_matches_known_points=True,
    )
