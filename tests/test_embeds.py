"""Tests for displayed copy and Discord size limits owned by embeds.py."""

from __future__ import annotations

from fractions import Fraction

from krillbot import embeds
from krillbot.boards import BoardPeriod, BoardStanding


def standing_with_score(user_id: int, score: int) -> BoardStanding:
    return BoardStanding(user_id=user_id, dives=1, total=score, average=Fraction(score), best=score)


def test_daily_board_shows_each_score_with_its_bearing() -> None:
    pages = embeds.daily_board_pages(
        95,
        [standing_with_score(20, 435), standing_with_score(21, 150)],
    )

    assert len(pages) == 1
    assert pages[0].title == "Daily #95"
    assert pages[0].description == (
        "1. <@20>: 435 points, Deep cut\n2. <@21>: 150 points, Plankton"
    )


def test_period_board_titles_are_owned_by_embeds() -> None:
    standings = [standing_with_score(20, 435)]

    assert embeds.period_board_pages(BoardPeriod.WEEK, standings)[0].title == "Week board"
    assert embeds.period_board_pages(BoardPeriod.MONTH, standings)[0].title == "Month board"
    assert embeds.period_board_pages(BoardPeriod.ALL, standings)[0].title == "All-time board"


def test_board_pages_hold_at_most_twenty_rows() -> None:
    standings = [standing_with_score(user_id, 100) for user_id in range(1, 42)]

    pages = embeds.period_board_pages(BoardPeriod.ALL, standings)

    assert [len(page.description.splitlines()) for page in pages] == [20, 20, 1]
    assert pages[2].description.startswith("41. ")


def test_board_pages_stay_inside_the_description_limit_for_unbounded_scores() -> None:
    enormous_score = int("9" * 1_900)
    standings = [standing_with_score(user_id, enormous_score) for user_id in range(1, 6)]

    pages = embeds.period_board_pages(BoardPeriod.ALL, standings)

    assert all(len(page.description) <= embeds.DISCORD_EMBED_DESCRIPTION_LIMIT for page in pages)
    assert sum(len(page.description.splitlines()) for page in pages) == 5


def test_a_row_longer_than_a_page_is_truncated_with_a_note() -> None:
    impossible_score = int("9" * 4_200)
    standings = [standing_with_score(20, impossible_score)]

    pages = embeds.period_board_pages(BoardPeriod.ALL, standings)

    assert len(pages) == 1
    assert len(pages[0].description) <= embeds.DISCORD_EMBED_DESCRIPTION_LIMIT
    assert pages[0].description.endswith(embeds.TRUNCATION_NOTE)


def test_long_result_history_is_truncated_inside_the_content_limit_with_a_note() -> None:
    results = [(daily_number, 435, "🐟🏮🏮🦑🐟🏮🦑") for daily_number in range(400, 0, -1)]

    message_text = embeds.user_results_message(results)

    assert len(message_text) <= embeds.DISCORD_MESSAGE_CONTENT_LIMIT
    assert message_text.endswith(embeds.TRUNCATION_NOTE)
    assert "#400: 435" in message_text


def test_short_result_history_is_not_truncated() -> None:
    message_text = embeds.user_results_message([(95, 435, "🐟🏮🏮🦑🐟🏮🦑")])

    assert message_text == "Your Krillion results in this server:\n#95: 435 points 🐟🏮🏮🦑🐟🏮🦑"
