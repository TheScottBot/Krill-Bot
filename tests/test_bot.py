"""Client construction and command-registration tests."""

from __future__ import annotations

import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from discord import app_commands

from krillbot import bot, config, daily, db
from krillbot.bot import KrillBot
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
