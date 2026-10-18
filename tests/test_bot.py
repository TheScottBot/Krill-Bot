"""Client construction and command-registration tests."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from discord import app_commands

from krillbot import bot, config, daily, db
from krillbot.bot import KrillBot
from krillbot.result_grammar import ParsedResult
from tests.fakes import FakeInteraction, complete_immediate_coroutine


def test_client_uses_default_intents_without_privileged_message_content() -> None:
    client = KrillBot()

    assert client.intents == client.intents.default()
    assert client.intents.message_content is False
    assert [command.name for command in client.tree.get_commands()] == [
        "dive",
        "setup",
        "help",
        "Log Krillion result",
    ]


def test_command_completion_log_contains_server_and_command_only(caplog) -> None:
    client = KrillBot()
    interaction = SimpleNamespace(guild_id=123, user=SimpleNamespace(id=456))
    command = SimpleNamespace(qualified_name="help")

    with caplog.at_level(logging.INFO, logger="krillbot"):
        complete_immediate_coroutine(client.on_app_command_completion(interaction, command))

    assert caplog.messages == ["[123] /help"]
    assert "456" not in caplog.text


def test_file_log_handler_rotates_and_uses_utf8(tmp_path: Path) -> None:
    log_path = tmp_path / "krillbot.log"

    handler = bot.build_file_log_handler(log_path)
    try:
        assert handler.maxBytes == 1_000_000
        assert handler.backupCount == 5
        assert handler.encoding.lower().replace("-", "") == "utf8"
    finally:
        handler.close()


def test_setup_hook_syncs_commands_to_each_development_server(monkeypatch) -> None:
    client = KrillBot()
    monkeypatch.setattr(config, "GUILD_IDS", (101, 202))
    sync_commands = AsyncMock(return_value=[SimpleNamespace()])
    monkeypatch.setattr(client.tree, "sync", sync_commands)

    complete_immediate_coroutine(client.setup_hook())

    assert [call.kwargs["guild"].id for call in sync_commands.await_args_list] == [
        101,
        202,
    ]


def test_command_error_sends_a_private_generic_response(caplog) -> None:
    client = KrillBot()
    interaction = FakeInteraction()
    interaction.command = SimpleNamespace(qualified_name="help")
    command_error = app_commands.AppCommandError("sensitive failure detail")

    with caplog.at_level(logging.ERROR, logger="krillbot"):
        complete_immediate_coroutine(client.on_app_command_error(interaction, command_error))

    response = interaction.last_response
    assert response.content == "Something went wrong. Please try again."
    assert response.ephemeral is True
    assert response.allowed_mentions is not None
    assert response.allowed_mentions.to_dict() == bot.NO_MENTIONS.to_dict()
    assert "sensitive failure detail" not in response.content


def test_daily_loop_checks_for_due_posts_every_minute() -> None:
    client = KrillBot()

    assert client.daily_loop.minutes == 1


def test_ready_starts_the_daily_loop_only_once(monkeypatch) -> None:
    client = KrillBot()
    start_loop = Mock()
    monkeypatch.setattr(client.daily_loop, "start", start_loop)
    monkeypatch.setattr(client.daily_loop, "is_running", Mock(side_effect=[False, True]))

    complete_immediate_coroutine(client.on_ready())
    complete_immediate_coroutine(client.on_ready())

    start_loop.assert_called_once_with()


def test_daily_loop_sends_due_posts_from_the_bots_database(monkeypatch) -> None:
    connection = db.initialise(":memory:")
    client = KrillBot(connection)
    post_due = AsyncMock()
    monkeypatch.setattr(daily, "post_due", post_due)
    try:
        complete_immediate_coroutine(client.daily_loop.coro(client))
    finally:
        connection.close()

    post_due.assert_awaited_once()
    awaited_client, awaited_connection, awaited_now = post_due.await_args.args
    assert awaited_client is client
    assert awaited_connection is connection
    assert awaited_now.tzinfo is not None


REMOVAL_LOGGED_AT = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)


def seed_removal_rows(connection) -> None:
    for guild_id in (10, 11):
        db.store_daily_result(
            connection,
            guild_id,
            20,
            ParsedResult(95, 435, "🐟🏮🏮🦑🐟🏮🦑", 435, True, True),
            REMOVAL_LOGGED_AT,
        )
        db.set_daily_post(
            connection,
            guild_id=guild_id,
            channel_id=300 + guild_id,
            post_clock=None,
            reset_clock=None,
            next_run=REMOVAL_LOGGED_AT,
        )


def test_removal_from_a_server_forgets_only_that_server(caplog) -> None:
    connection = db.initialise(":memory:")
    client = KrillBot(connection)
    try:
        seed_removal_rows(connection)
        with caplog.at_level(logging.INFO, logger="krillbot"):
            complete_immediate_coroutine(client.on_guild_remove(SimpleNamespace(id=10)))
        remaining_guilds = [
            row[0] for row in connection.execute("SELECT guild_id FROM daily_results")
        ]
        removed_post = db.daily_post_setting(connection, guild_id=10)
        kept_post = db.daily_post_setting(connection, guild_id=11)
    finally:
        connection.close()

    assert remaining_guilds == [11]
    assert removed_post is None
    assert kept_post is not None
    assert caplog.messages == [
        "[10] Forgot the server: 1 result, 1 daily post, 0 settings (guild-removed)"
    ]


def test_a_deleted_channel_stops_its_servers_daily_post() -> None:
    connection = db.initialise(":memory:")
    client = KrillBot(connection)
    try:
        seed_removal_rows(connection)
        complete_immediate_coroutine(
            client.on_guild_channel_delete(SimpleNamespace(id=310, guild=SimpleNamespace(id=10)))
        )
        stopped_post = db.daily_post_setting(connection, guild_id=10)
        kept_post = db.daily_post_setting(connection, guild_id=11)
        result_count = connection.execute("SELECT COUNT(*) FROM daily_results").fetchone()[0]
    finally:
        connection.close()

    assert stopped_post is None
    assert kept_post is not None
    assert result_count == 2


def test_a_deleted_thread_stops_its_servers_daily_post() -> None:
    connection = db.initialise(":memory:")
    client = KrillBot(connection)
    try:
        seed_removal_rows(connection)
        complete_immediate_coroutine(
            client.on_raw_thread_delete(SimpleNamespace(thread_id=311, guild_id=11))
        )
        stopped_post = db.daily_post_setting(connection, guild_id=11)
        kept_post = db.daily_post_setting(connection, guild_id=10)
    finally:
        connection.close()

    assert stopped_post is None
    assert kept_post is not None
