"""Application-command tests for the KE1 surface."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

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


def setup_commands() -> list[discord.app_commands.Command[Any, ..., Any]]:
    return [
        setup_command
        for setup_command in commands.setup_group.walk_commands()
        if isinstance(setup_command, discord.app_commands.Command)
    ]


def test_setup_is_server_only_and_defaults_to_manage_server() -> None:
    assert commands.setup_group.guild_only is True
    assert commands.setup_group.default_permissions is not None
    assert commands.setup_group.default_permissions.manage_guild is True
    assert sorted(setup_command.name for setup_command in setup_commands()) == [
        "here",
        "show",
        "show",
        "stop",
        "visibility",
    ]


def test_every_setup_command_refuses_a_member_without_manage_server() -> None:
    refused_interaction = FakeInteraction(guild_id=10, permissions=discord.Permissions.none())
    permitted_interaction = FakeInteraction(
        guild_id=10,
        permissions=discord.Permissions(manage_guild=True),
    )

    for setup_command in setup_commands():
        assert setup_command.checks, setup_command.name
        for permission_check in setup_command.checks:
            try:
                permission_check(refused_interaction)
            except discord.app_commands.MissingPermissions:
                pass
            else:
                raise AssertionError(f"/setup {setup_command.name} accepted a non-manager")
            assert permission_check(permitted_interaction) is True


def test_setup_visibility_shown_reveals_today_to_a_viewer_who_has_not_logged() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    try:
        complete_immediate_coroutine(
            commands.log_result_command.callback(
                FakeInteraction(guild_id=10, user_id=20, client=client),
                DAILY_RESULT_TEXT,
            )
        )
        manager_interaction = FakeInteraction(guild_id=10, user_id=30, client=client)
        complete_immediate_coroutine(
            commands.setup_visibility_command.callback(manager_interaction, "shown")
        )
        viewing_interaction = FakeInteraction(guild_id=10, user_id=21, client=client)
        complete_immediate_coroutine(commands.today_command.callback(viewing_interaction))
    finally:
        connection.close()

    assert manager_interaction.last_response.content == (
        "Scores on /dive today are now shown to everyone in this server."
    )
    assert manager_interaction.last_response.ephemeral is True
    assert manager_interaction.last_response.allowed_mentions is not None
    assert viewing_interaction.last_response.embed is not None
    assert viewing_interaction.last_response.embed.description == ("1. <@20>: 435 points, Deep cut")


def test_setup_visibility_hidden_restores_the_default() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    manager_interaction = FakeInteraction(guild_id=10, user_id=30, client=client)
    try:
        complete_immediate_coroutine(
            commands.setup_visibility_command.callback(manager_interaction, "shown")
        )
        complete_immediate_coroutine(
            commands.setup_visibility_command.callback(manager_interaction, "hidden")
        )
        hidden_setting = db.hide_scores_until_logged(connection, guild_id=10)
    finally:
        connection.close()

    assert hidden_setting is True
    assert manager_interaction.last_response.content == (
        "Scores on /dive today are now hidden until each viewer logs their own result."
    )


def test_setup_show_reports_this_servers_settings_privately() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    manager_interaction = FakeInteraction(guild_id=10, user_id=30, client=client)
    try:
        complete_immediate_coroutine(
            commands.setup_visibility_command.callback(
                FakeInteraction(guild_id=11, user_id=30, client=client),
                "shown",
            )
        )
        complete_immediate_coroutine(commands.setup_show_command.callback(manager_interaction))
    finally:
        connection.close()

    response = manager_interaction.last_response
    assert response.ephemeral is True
    assert response.allowed_mentions is not None
    assert response.allowed_mentions.to_dict() == discord.AllowedMentions.none().to_dict()
    assert response.embed is not None
    assert response.embed.title == "Krill Bot settings"
    assert [(field.name, field.value) for field in response.embed.fields] == [
        ("Today's scores", "Hidden until each viewer logs their own result"),
        ("Daily post", "Not set up"),
    ]


def daily_setup_commands() -> list[discord.app_commands.Command[Any, ..., Any]]:
    return [
        daily_command
        for daily_command in commands.daily_setup_group.walk_commands()
        if isinstance(daily_command, discord.app_commands.Command)
    ]


def stored_daily_post(connection: Any, guild_id: int = 10) -> tuple[Any, ...] | None:
    row: tuple[Any, ...] | None = connection.execute(
        "SELECT channel_id, clock, reset_clock, next_run FROM daily_posts WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()
    return row


def test_daily_setup_offers_here_stop_and_show_each_requiring_manage_server() -> None:
    refused_interaction = FakeInteraction(guild_id=10, permissions=discord.Permissions.none())

    assert sorted(daily_command.name for daily_command in daily_setup_commands()) == [
        "here",
        "show",
        "stop",
    ]
    for daily_command in daily_setup_commands():
        assert daily_command.checks, daily_command.name
        for permission_check in daily_command.checks:
            try:
                permission_check(refused_interaction)
            except discord.app_commands.MissingPermissions:
                continue
            raise AssertionError(f"/setup daily {daily_command.name} accepted a non-manager")


def test_daily_here_without_times_follows_the_defaults_and_replies_privately(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(commands.config, "DAILY_POST_TIME", "17:00")
    monkeypatch.setattr(commands.config, "DAILY_RESET_TIME", "04:00")
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        channel_id=300,
        client=SimpleNamespace(database_connection=connection),
    )
    before_setup = datetime.now(UTC)
    try:
        complete_immediate_coroutine(commands.daily_here_command.callback(interaction, None, None))
        stored_row = stored_daily_post(connection)
    finally:
        connection.close()

    assert stored_row is not None
    channel_id, post_clock, reset_clock, next_run = stored_row
    assert (channel_id, post_clock, reset_clock) == (300, None, None)
    assert before_setup < datetime.fromisoformat(next_run) <= before_setup + timedelta(days=1)
    assert interaction.last_response.content == (
        "The daily post will go to <#300> at 17:00 (the default), "
        "with the dive resetting at 04:00 (the default)."
    )
    assert interaction.last_response.ephemeral is True
    assert interaction.last_response.allowed_mentions is not None


def test_daily_here_stores_the_servers_own_times() -> None:
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        channel_id=300,
        client=SimpleNamespace(database_connection=connection),
    )
    try:
        complete_immediate_coroutine(
            commands.daily_here_command.callback(interaction, "6pm", "5:30am")
        )
        stored_row = stored_daily_post(connection)
    finally:
        connection.close()

    assert stored_row is not None
    assert stored_row[:3] == (300, "18:00", "05:30")
    assert interaction.last_response.content == (
        "The daily post will go to <#300> at 18:00, with the dive resetting at 05:30."
    )


def test_daily_here_says_when_the_post_has_moved_channel() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    try:
        complete_immediate_coroutine(
            commands.daily_here_command.callback(
                FakeInteraction(guild_id=10, channel_id=300, client=client), "6pm", "4am"
            )
        )
        moving_interaction = FakeInteraction(guild_id=10, channel_id=301, client=client)
        complete_immediate_coroutine(
            commands.daily_here_command.callback(moving_interaction, "6pm", "4am")
        )
    finally:
        connection.close()

    assert moving_interaction.last_response.content == (
        "The daily post will go to <#301> at 18:00, with the dive resetting at 04:00.\n"
        "It has moved here from <#300>."
    )


def test_daily_here_refuses_an_unreadable_time_and_stores_nothing() -> None:
    connection = db.initialise(":memory:")
    interaction = FakeInteraction(
        guild_id=10,
        channel_id=300,
        client=SimpleNamespace(database_connection=connection),
    )
    try:
        complete_immediate_coroutine(
            commands.daily_here_command.callback(interaction, "6pm", "teatime")
        )
        stored_row = stored_daily_post(connection)
    finally:
        connection.close()

    assert stored_row is None
    assert interaction.last_response.content == (
        "I can't read that as a time of day. Try 5pm, 6:30pm or 17:00."
    )
    assert interaction.last_response.ephemeral is True


def test_daily_stop_is_idempotent_and_says_what_happened() -> None:
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    first_stop = FakeInteraction(guild_id=10, client=client)
    second_stop = FakeInteraction(guild_id=10, client=client)
    try:
        complete_immediate_coroutine(
            commands.daily_here_command.callback(
                FakeInteraction(guild_id=10, channel_id=300, client=client), None, None
            )
        )
        complete_immediate_coroutine(commands.daily_stop_command.callback(first_stop))
        complete_immediate_coroutine(commands.daily_stop_command.callback(second_stop))
        stored_row = stored_daily_post(connection)
    finally:
        connection.close()

    assert stored_row is None
    assert first_stop.last_response.content == "The daily post has stopped."
    assert second_stop.last_response.content == "There is no daily post to stop."
    assert second_stop.last_response.ephemeral is True


def test_daily_show_describes_the_post_or_its_absence(monkeypatch: Any) -> None:
    monkeypatch.setattr(commands.config, "DAILY_POST_TIME", "17:00")
    monkeypatch.setattr(commands.config, "DAILY_RESET_TIME", "04:00")
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    before_interaction = FakeInteraction(guild_id=10, client=client)
    after_interaction = FakeInteraction(guild_id=10, client=client)
    try:
        complete_immediate_coroutine(commands.daily_show_command.callback(before_interaction))
        complete_immediate_coroutine(
            commands.daily_here_command.callback(
                FakeInteraction(guild_id=10, channel_id=300, client=client), None, "5am"
            )
        )
        complete_immediate_coroutine(commands.daily_show_command.callback(after_interaction))
    finally:
        connection.close()

    assert before_interaction.last_response.content == (
        "There is no daily post here. /setup daily here posts one in that channel."
    )
    assert after_interaction.last_response.content == (
        "The daily post goes to <#300> at 17:00 (the default), with the dive resetting at 05:00."
    )
    assert after_interaction.last_response.ephemeral is True


def test_setup_show_reports_a_daily_post_that_follows_the_default_time(
    monkeypatch: Any,
) -> None:
    monkeypatch.setattr(commands.config, "DAILY_POST_TIME", "17:00")
    monkeypatch.setattr(commands.config, "DAILY_RESET_TIME", "04:00")
    connection = db.initialise(":memory:")
    client = SimpleNamespace(database_connection=connection)
    show_interaction = FakeInteraction(guild_id=10, client=client)
    try:
        complete_immediate_coroutine(
            commands.daily_here_command.callback(
                FakeInteraction(guild_id=10, channel_id=300, client=client), None, None
            )
        )
        complete_immediate_coroutine(commands.setup_show_command.callback(show_interaction))
    finally:
        connection.close()

    assert show_interaction.last_response.embed is not None
    assert [(field.name, field.value) for field in show_interaction.last_response.embed.fields] == [
        ("Today's scores", "Hidden until each viewer logs their own result"),
        (
            "Daily post",
            "<#300> at 17:00 (the default), with the dive resetting at 04:00 (the default)",
        ),
    ]
