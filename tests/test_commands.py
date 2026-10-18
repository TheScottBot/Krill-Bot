"""Application-command tests for the KE1 surface."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from types import SimpleNamespace

import discord

from krillbot import commands, db
from krillbot.result_grammar import ParsedResult
from tests.fakes import FakeInteraction, FakeMessage, complete_immediate_coroutine

DAILY_RESULT_TEXT = "Krillion #95 🦐\n435\n\n🐟🏮🏮🦑🐟🏮🦑"


def test_help_identifies_the_bot_as_unofficial_and_disables_mentions() -> None:
    interaction = FakeInteraction()

    complete_immediate_coroutine(commands.help_command.callback(interaction))

    response = interaction.last_response
    assert response.embed is not None
    assert response.embed.title == "Krill Bot"
    assert "unofficial" in response.embed.description.lower()
    assert response.allowed_mentions is not None
    assert response.allowed_mentions.to_dict() == discord.AllowedMentions.none().to_dict()


def test_dive_log_stores_result_and_replies_privately() -> None:
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        user_id=20,
        client=SimpleNamespace(database_connection=connection),
    )
    try:
        complete_immediate_coroutine(
            commands.log_result_command.callback(interaction, DAILY_RESULT_TEXT)
        )
        stored_row = connection.execute(
            "SELECT guild_id, user_id, daily_number, score, emoji_row FROM daily_results"
        ).fetchone()
    finally:
        connection.close()

    assert stored_row == (10, 20, 95, 435, "🐟🏮🏮🦑🐟🏮🦑")
    assert interaction.last_response.content == "Logged daily #95 with 435 points."
    assert interaction.last_response.ephemeral is True


def test_dive_log_replaces_same_daily_result_and_says_so() -> None:
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        user_id=20,
        client=SimpleNamespace(database_connection=connection),
    )
    try:
        complete_immediate_coroutine(
            commands.log_result_command.callback(interaction, DAILY_RESULT_TEXT)
        )
        second_interaction = FakeInteraction(
            guild_id=10,
            user_id=20,
            client=SimpleNamespace(database_connection=connection),
        )
        complete_immediate_coroutine(
            commands.log_result_command.callback(
                second_interaction,
                "Krillion #95 🦐\n436\n\n🐟🏮🏮🦑🐟🏮🦑",
            )
        )
    finally:
        connection.close()

    assert second_interaction.last_response.content == "Replaced daily #95 with 436 points."
    assert second_interaction.last_response.ephemeral is True


def test_refused_paste_stores_nothing_and_logs_only_reason_and_server(caplog) -> None:
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        user_id=20,
        client=SimpleNamespace(database_connection=connection),
    )
    supplied_text = "private conversation that is not a result"
    try:
        with caplog.at_level(logging.INFO, logger="krillbot"):
            complete_immediate_coroutine(
                commands.log_result_command.callback(interaction, supplied_text)
            )
        stored_count = connection.execute("SELECT COUNT(*) FROM daily_results").fetchone()[0]
    finally:
        connection.close()

    assert stored_count == 0
    assert interaction.last_response.content == (
        "this doesn't look like a result, feel free to message me on Discord to update the bot "
        "if its outdated."
    )
    assert interaction.last_response.ephemeral is True
    assert caplog.messages == ["[10] Refused result: not-a-result"]
    assert supplied_text not in caplog.text
    assert "20" not in caplog.text


def test_message_menu_refuses_a_message_written_by_someone_else() -> None:
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        user_id=20,
        client=SimpleNamespace(database_connection=connection),
    )
    selected_message = FakeMessage(author_id=21, content=DAILY_RESULT_TEXT)
    try:
        complete_immediate_coroutine(
            commands.log_message_command.callback(interaction, selected_message)
        )
        stored_count = connection.execute("SELECT COUNT(*) FROM daily_results").fetchone()[0]
    finally:
        connection.close()

    assert stored_count == 0
    assert interaction.last_response.content == "You can only log a result from your own message."
    assert interaction.last_response.ephemeral is True


def test_message_menu_logs_the_callers_own_message() -> None:
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        user_id=20,
        client=SimpleNamespace(database_connection=connection),
    )
    selected_message = FakeMessage(author_id=20, content=DAILY_RESULT_TEXT)
    try:
        complete_immediate_coroutine(
            commands.log_message_command.callback(interaction, selected_message)
        )
        stored_count = connection.execute("SELECT COUNT(*) FROM daily_results").fetchone()[0]
    finally:
        connection.close()

    assert stored_count == 1
    assert interaction.last_response.ephemeral is True


def test_dive_me_lists_only_the_callers_results_from_this_server() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    first_interaction = FakeInteraction(guild_id=10, user_id=20, client=client)
    other_server_interaction = FakeInteraction(guild_id=11, user_id=20, client=client)
    try:
        complete_immediate_coroutine(
            commands.log_result_command.callback(first_interaction, DAILY_RESULT_TEXT)
        )
        complete_immediate_coroutine(
            commands.log_result_command.callback(
                other_server_interaction,
                "Krillion #96 🦐\n100\n\n🫧🫧🫧🫧🫧🫧🫧",
            )
        )
        viewing_interaction = FakeInteraction(guild_id=10, user_id=20, client=client)
        complete_immediate_coroutine(commands.me_command.callback(viewing_interaction))
    finally:
        connection.close()

    assert "#95: 435" in viewing_interaction.last_response.content
    assert "#96" not in viewing_interaction.last_response.content
    assert viewing_interaction.last_response.ephemeral is True


def test_today_hides_scores_until_the_viewer_logs_current_result() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    author_interaction = FakeInteraction(guild_id=10, user_id=20, client=client)
    try:
        complete_immediate_coroutine(
            commands.log_result_command.callback(author_interaction, DAILY_RESULT_TEXT)
        )
        viewing_interaction = FakeInteraction(guild_id=10, user_id=21, client=client)
        complete_immediate_coroutine(commands.today_command.callback(viewing_interaction))
    finally:
        connection.close()

    assert viewing_interaction.last_response.content == (
        "Today's scores are hidden until you log your own result."
    )
    assert viewing_interaction.last_response.ephemeral is True


def test_today_shows_current_board_after_the_viewer_logs() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    interaction = FakeInteraction(guild_id=10, user_id=20, client=client)
    try:
        complete_immediate_coroutine(
            commands.log_result_command.callback(interaction, DAILY_RESULT_TEXT)
        )
        viewing_interaction = FakeInteraction(guild_id=10, user_id=20, client=client)
        complete_immediate_coroutine(commands.today_command.callback(viewing_interaction))
    finally:
        connection.close()

    response_embed = viewing_interaction.last_response.embed
    assert response_embed is not None
    assert response_embed.title == "Daily #95"
    assert "435" in response_embed.description
    assert viewing_interaction.last_response.ephemeral is True
    assert response_embed.description == "1. <@20>: 435 points, Deep cut"


def test_board_command_pages_long_standings_and_disables_mentions() -> None:
    connection = db.initialise(":memory:")
    logged_at = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    try:
        for user_id in range(1, 23):
            db.store_daily_result(
                connection,
                10,
                user_id,
                ParsedResult(95, user_id, "🆕", 0, False, False),
                logged_at,
            )
        interaction = FakeInteraction(
            guild_id=10,
            user_id=1,
            client=SimpleNamespace(database_connection=connection),
        )
        complete_immediate_coroutine(commands.board_command.callback(interaction, "week"))
    finally:
        connection.close()

    assert interaction.last_response.embed is not None
    assert interaction.last_response.ephemeral is True
    assert len(interaction.followup.sent_responses) == 1
    assert interaction.followup.sent_responses[0].ephemeral is True
    assert interaction.followup.sent_responses[0].allowed_mentions is not None
    assert (
        interaction.followup.sent_responses[0].allowed_mentions.to_dict()
        == discord.AllowedMentions.none().to_dict()
    )


def test_streak_command_reports_current_and_longest_for_caller() -> None:
    connection = db.initialise(":memory:")
    logged_at = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    try:
        for daily_number in (91, 92, 94, 95):
            db.store_daily_result(
                connection,
                10,
                20,
                ParsedResult(daily_number, 100, "🆕", 0, False, False),
                logged_at,
            )
        interaction = FakeInteraction(
            guild_id=10,
            user_id=20,
            client=SimpleNamespace(database_connection=connection),
        )
        complete_immediate_coroutine(commands.streak_command.callback(interaction, None))
    finally:
        connection.close()

    assert interaction.last_response.content == "Your current streak is 2; your longest is 2."
    assert interaction.last_response.ephemeral is True
