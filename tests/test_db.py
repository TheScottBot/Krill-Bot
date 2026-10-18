"""SQLite schema and version contract tests."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime, timedelta

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


DUE_AT = datetime(2026, 10, 18, 16, 0, tzinfo=UTC)


def test_version_one_database_upgrades_keeping_rows_and_allowing_default_times() -> None:
    connection = sqlite3.connect(":memory:")
    try:
        for statement in db.SCHEMA_VERSION_1_STATEMENTS:
            connection.execute(statement)
        connection.execute("PRAGMA user_version = 1")
        connection.execute(
            "INSERT INTO daily_posts (guild_id, channel_id, clock, next_run) VALUES (?, ?, ?, ?)",
            (10, 300, "09:00", DUE_AT.isoformat()),
        )
        connection.commit()

        db.initialise_connection(connection)
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        preserved_setting = db.daily_post_setting(connection, guild_id=10)
        db.set_daily_post(
            connection,
            guild_id=11,
            channel_id=301,
            post_clock=None,
            reset_clock=None,
            next_run=DUE_AT,
        )
        default_setting = db.daily_post_setting(connection, guild_id=11)
    finally:
        connection.close()

    assert version == db.SCHEMA_VERSION == 2
    assert preserved_setting == db.DailyPostSetting(channel_id=300, clock="09:00")
    assert default_setting == db.DailyPostSetting(channel_id=301, clock=None, reset_clock=None)


def test_set_daily_post_moves_a_servers_post_and_reports_the_previous_channel() -> None:
    connection = db.initialise(":memory:")
    try:
        first_previous = db.set_daily_post(
            connection,
            guild_id=10,
            channel_id=300,
            post_clock="18:00",
            reset_clock="05:00",
            next_run=DUE_AT,
        )
        second_previous = db.set_daily_post(
            connection,
            guild_id=10,
            channel_id=301,
            post_clock=None,
            reset_clock="05:00",
            next_run=DUE_AT,
        )
        stored_setting = db.daily_post_setting(connection, guild_id=10)
        row_count = connection.execute("SELECT COUNT(*) FROM daily_posts").fetchone()[0]
    finally:
        connection.close()

    assert first_previous is None
    assert second_previous == 300
    assert stored_setting == db.DailyPostSetting(channel_id=301, clock=None, reset_clock="05:00")
    assert row_count == 1


def test_stop_daily_post_is_idempotent_and_scoped_to_one_server() -> None:
    connection = db.initialise(":memory:")
    try:
        for guild_id in (10, 11):
            db.set_daily_post(
                connection,
                guild_id=guild_id,
                channel_id=300 + guild_id,
                post_clock=None,
                reset_clock=None,
                next_run=DUE_AT,
            )

        assert db.stop_daily_post(connection, guild_id=10) is True
        assert db.stop_daily_post(connection, guild_id=10) is False
        assert db.daily_post_setting(connection, guild_id=10) is None
        assert db.daily_post_setting(connection, guild_id=11) is not None
    finally:
        connection.close()


def test_due_daily_posts_are_those_whose_next_run_has_arrived_and_can_move_on() -> None:
    connection = db.initialise(":memory:")
    later = DUE_AT + timedelta(hours=1)
    try:
        db.set_daily_post(
            connection,
            guild_id=10,
            channel_id=300,
            post_clock="17:00",
            reset_clock=None,
            next_run=DUE_AT,
        )
        db.set_daily_post(
            connection,
            guild_id=11,
            channel_id=301,
            post_clock=None,
            reset_clock="05:00",
            next_run=later,
        )
        due_now = db.daily_posts_due(connection, now=DUE_AT)
        db.move_daily_post_on(connection, guild_id=10, next_run=DUE_AT + timedelta(days=1))
        due_after_moving_on = db.daily_posts_due(connection, now=later)
    finally:
        connection.close()

    assert due_now == [
        db.DailyPostSchedule(
            guild_id=10,
            channel_id=300,
            post_clock="17:00",
            reset_clock=None,
            next_run=DUE_AT,
        )
    ]
    assert [schedule.guild_id for schedule in due_after_moving_on] == [11]


def test_daily_numbers_logged_in_a_window_are_scoped_to_one_server() -> None:
    connection = db.initialise(":memory:")
    window_start = datetime(2026, 10, 17, 3, 0, tzinfo=UTC)
    window_end = datetime(2026, 10, 18, 3, 0, tzinfo=UTC)
    try:
        for guild_id, daily_number, logged_at in (
            (10, 94, window_start - timedelta(seconds=1)),
            (10, 95, window_start),
            (10, 95, window_end - timedelta(microseconds=1)),
            (10, 96, window_end),
            (11, 95, window_start + timedelta(hours=1)),
        ):
            db.store_daily_result(
                connection,
                guild_id,
                daily_number * 10 + guild_id + logged_at.second,
                ParsedResult(daily_number, 100, "🫧🫧🫧🫧🫧🫧🫧", 70, True, False),
                logged_at,
            )

        numbers = db.daily_numbers_logged_between(
            connection,
            guild_id=10,
            start=window_start,
            end=window_end,
        )
    finally:
        connection.close()

    assert numbers == {95}
