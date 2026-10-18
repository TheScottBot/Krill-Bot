"""SQLite schema and version contract tests."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from krillbot import db
from krillbot.result_grammar import ParsedResult


def test_initialise_creates_the_current_schema_in_memory() -> None:
    connection = db.initialise(":memory:")
    try:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
    finally:
        connection.close()

    assert version == db.SCHEMA_VERSION
    assert tables == {"daily_results", "daily_posts", "guild_settings"}


def test_initialise_refuses_a_newer_schema_version() -> None:
    connection = sqlite3.connect(":memory:")
    connection.execute(f"PRAGMA user_version = {db.SCHEMA_VERSION + 1}")

    with pytest.raises(db.NewerSchemaError):
        db.initialise_connection(connection)

    connection.close()


def test_store_daily_result_writes_only_permitted_columns_and_reports_replacement() -> None:
    connection = db.initialise(":memory:")
    first_result = ParsedResult(95, 435, "🐟🏮🏮🦑🐟🏮🦑", 435, True, True)
    replacement_result = ParsedResult(95, 440, "🐟🏮🏮🦑🐟🏮🦑", 435, True, False)
    logged_at = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    try:
        assert db.store_daily_result(connection, 10, 20, first_result, logged_at) is False
        assert db.store_daily_result(connection, 10, 20, replacement_result, logged_at) is True
        stored_rows = connection.execute("SELECT * FROM daily_results").fetchall()
    finally:
        connection.close()

    assert stored_rows == [(10, 20, 95, 440, "🐟🏮🏮🦑🐟🏮🦑", logged_at.isoformat())]


def test_user_results_are_scoped_to_server_and_ordered_newest_first() -> None:
    connection = db.initialise(":memory:")
    logged_at = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    try:
        db.store_daily_result(
            connection,
            10,
            20,
            ParsedResult(94, 235, "🏮🫧🐟🫧🐟🫧🦑", 235, True, True),
            logged_at,
        )
        db.store_daily_result(
            connection,
            10,
            20,
            ParsedResult(95, 435, "🐟🏮🏮🦑🐟🏮🦑", 435, True, True),
            logged_at,
        )
        db.store_daily_result(
            connection,
            11,
            20,
            ParsedResult(96, 100, "🫧🫧🫧🫧🫧🫧🫧", 70, True, False),
            logged_at,
        )

        stored_results = db.user_results(connection, guild_id=10, user_id=20)
    finally:
        connection.close()

    assert [(result.daily_number, result.score) for result in stored_results] == [
        (95, 435),
        (94, 235),
    ]


def test_board_reads_and_latest_number_are_scoped_to_server() -> None:
    connection = db.initialise(":memory:")
    logged_at = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    try:
        db.store_daily_result(
            connection,
            10,
            20,
            ParsedResult(95, 435, "🐟🏮🏮🦑🐟🏮🦑", 435, True, True),
            logged_at,
        )
        db.store_daily_result(
            connection,
            11,
            21,
            ParsedResult(100, 700, "🏮🏮🏮🏮🏮🏮🏮", 595, True, False),
            logged_at,
        )

        entries = db.server_board_entries(connection, guild_id=10)
        latest_number = db.latest_daily_number(connection, guild_id=10)
    finally:
        connection.close()

    assert [(entry.user_id, entry.daily_number, entry.score) for entry in entries] == [
        (20, 95, 435)
    ]
    assert latest_number == 95


def test_visibility_defaults_to_hidden_and_detects_viewers_result() -> None:
    connection = db.initialise(":memory:")
    logged_at = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
    try:
        db.store_daily_result(
            connection,
            10,
            20,
            ParsedResult(95, 435, "🐟🏮🏮🦑🐟🏮🦑", 435, True, True),
            logged_at,
        )

        assert db.hide_scores_until_logged(connection, guild_id=10) is True
        assert (
            db.user_has_daily_result(
                connection,
                guild_id=10,
                user_id=20,
                daily_number=95,
            )
            is True
        )
        assert (
            db.user_has_daily_result(
                connection,
                guild_id=10,
                user_id=21,
                daily_number=95,
            )
            is False
        )
    finally:
        connection.close()


def test_visibility_setting_is_stored_per_server_and_is_idempotent() -> None:
    connection = db.initialise(":memory:")
    try:
        db.set_hide_scores_until_logged(connection, guild_id=10, hide_until_logged=False)
        db.set_hide_scores_until_logged(connection, guild_id=10, hide_until_logged=False)

        assert db.hide_scores_until_logged(connection, guild_id=10) is False
        assert db.hide_scores_until_logged(connection, guild_id=11) is True
        assert connection.execute("SELECT COUNT(*) FROM guild_settings").fetchone() == (1,)

        db.set_hide_scores_until_logged(connection, guild_id=10, hide_until_logged=True)

        assert db.hide_scores_until_logged(connection, guild_id=10) is True
    finally:
        connection.close()


def test_daily_post_setting_is_absent_until_a_server_sets_one_up() -> None:
    connection = db.initialise(":memory:")
    try:
        connection.execute(
            "INSERT INTO daily_posts (guild_id, channel_id, clock, next_run) VALUES (?, ?, ?, ?)",
            (11, 300, "09:00", "2026-10-19T08:00:00+00:00"),
        )

        assert db.daily_post_setting(connection, guild_id=10) is None
        assert db.daily_post_setting(connection, guild_id=11) == db.DailyPostSetting(
            channel_id=300,
            clock="09:00",
        )
    finally:
        connection.close()
