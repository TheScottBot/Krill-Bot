"""Tests for the daily post: due times, yesterday's board, skipping and moving on."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import discord
import pytest

from krillbot import config, daily, db
from krillbot.result_grammar import ParsedResult
from tests.fakes import FakeChannel, FakeClient, complete_immediate_coroutine

# 17:00 in London on 18 October 2026 is 16:00 UTC; the 04:00 resets either side
# of the previous day are 03:00 UTC on 17 and 18 October.
POST_DUE_AT = datetime(2026, 10, 18, 16, 0, tzinfo=UTC)
PREVIOUS_RESET = datetime(2026, 10, 18, 3, 0, tzinfo=UTC)
RESET_BEFORE_THAT = datetime(2026, 10, 17, 3, 0, tzinfo=UTC)
CHANNEL_ID = 300


@pytest.fixture
def connection(monkeypatch: pytest.MonkeyPatch) -> Iterator[sqlite3.Connection]:
    monkeypatch.setattr(config, "DAILY_POST_TIME", "17:00")
    monkeypatch.setattr(config, "DAILY_RESET_TIME", "04:00")
    database_connection = db.initialise(":memory:")
    yield database_connection
    database_connection.close()


def set_up_post(
    connection: sqlite3.Connection,
    *,
    guild_id: int = 10,
    channel_id: int = CHANNEL_ID,
    post_clock: str | None = None,
    reset_clock: str | None = None,
    next_run: datetime = POST_DUE_AT,
) -> None:
    db.set_daily_post(
        connection,
        guild_id=guild_id,
        channel_id=channel_id,
        post_clock=post_clock,
        reset_clock=reset_clock,
        next_run=next_run,
    )


def log_result(
    connection: sqlite3.Connection,
    *,
    guild_id: int = 10,
    user_id: int,
    daily_number: int,
    score: int,
    logged_at: datetime,
) -> None:
    db.store_daily_result(
        connection,
        guild_id,
        user_id,
        ParsedResult(daily_number, score, "🫧🫧🫧🫧🫧🫧🫧", 70, True, False),
        logged_at,
    )


def post_due(connection: sqlite3.Connection, client: FakeClient, now: datetime) -> None:
    complete_immediate_coroutine(daily.post_due(client, connection, now))


def next_run_of(connection: sqlite3.Connection, guild_id: int = 10) -> datetime:
    row = connection.execute(
        "SELECT next_run FROM daily_posts WHERE guild_id = ?", (guild_id,)
    ).fetchone()
    return datetime.fromisoformat(row[0])


def sent_description(channel: FakeChannel) -> str:
    sent_embed = channel.sent_messages[0].embed
    assert sent_embed is not None
    assert sent_embed.description is not None
    return sent_embed.description


def test_nothing_is_posted_before_the_post_is_due(connection: sqlite3.Connection) -> None:
    channel = FakeChannel(channel_id=CHANNEL_ID)
    set_up_post(connection)

    post_due(connection, FakeClient(channel), POST_DUE_AT - timedelta(minutes=1))

    assert channel.sent_messages == []
    assert next_run_of(connection) == POST_DUE_AT


def test_a_due_post_is_sent_without_pings_and_moves_on_to_tomorrow(
    connection: sqlite3.Connection,
) -> None:
    channel = FakeChannel(channel_id=CHANNEL_ID)
    set_up_post(connection)

    post_due(connection, FakeClient(channel), POST_DUE_AT)

    assert len(channel.sent_messages) == 1
    allowed_mentions = channel.sent_messages[0].allowed_mentions
    assert allowed_mentions is not None
    assert allowed_mentions.to_dict() == discord.AllowedMentions.none().to_dict()
    assert "https://krillion.io" in sent_description(channel)
    assert next_run_of(connection) == POST_DUE_AT + timedelta(days=1)


def test_a_servers_own_post_time_is_used_for_the_next_run(
    connection: sqlite3.Connection,
) -> None:
    set_up_post(connection, post_clock="09:30")

    post_due(connection, FakeClient(FakeChannel(channel_id=CHANNEL_ID)), POST_DUE_AT)

    assert next_run_of(connection) == datetime(2026, 10, 19, 8, 30, tzinfo=UTC)


def test_the_environment_post_time_is_used_when_a_server_chose_none(
    connection: sqlite3.Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(config, "DAILY_POST_TIME", "18:15")
    set_up_post(connection)

    post_due(connection, FakeClient(FakeChannel(channel_id=CHANNEL_ID)), POST_DUE_AT)

    assert next_run_of(connection) == datetime(2026, 10, 18, 17, 15, tzinfo=UTC)


def test_the_post_carries_yesterdays_board_from_this_server_only(
    connection: sqlite3.Connection,
) -> None:
    channel = FakeChannel(channel_id=CHANNEL_ID)
    set_up_post(connection)
    log_result(connection, user_id=20, daily_number=95, score=435, logged_at=RESET_BEFORE_THAT)
    log_result(
        connection,
        user_id=21,
        daily_number=95,
        score=150,
        logged_at=PREVIOUS_RESET + timedelta(hours=2),
    )
    log_result(connection, user_id=22, daily_number=96, score=300, logged_at=PREVIOUS_RESET)
    log_result(
        connection,
        guild_id=11,
        user_id=23,
        daily_number=95,
        score=600,
        logged_at=RESET_BEFORE_THAT,
    )

    post_due(connection, FakeClient(channel), POST_DUE_AT)

    description = sent_description(channel)
    assert "Yesterday's board, daily #95" in description
    assert "1. <@20>: 435 points, Deep cut" in description
    assert "2. <@21>: 150 points, Plankton" in description
    assert "<@22>" not in description
    assert "<@23>" not in description


def test_a_servers_own_reset_time_chooses_yesterdays_dive(
    connection: sqlite3.Connection,
) -> None:
    channel = FakeChannel(channel_id=CHANNEL_ID)
    set_up_post(connection, reset_clock="10:00")
    log_result(
        connection,
        user_id=20,
        daily_number=95,
        score=435,
        logged_at=datetime(2026, 10, 17, 9, 30, tzinfo=UTC),
    )

    post_due(connection, FakeClient(channel), POST_DUE_AT)

    assert "daily #95" in sent_description(channel)


def test_the_post_says_so_when_nobody_logged_yesterday(
    connection: sqlite3.Connection,
) -> None:
    channel = FakeChannel(channel_id=CHANNEL_ID)
    set_up_post(connection)
    log_result(
        connection,
        user_id=20,
        daily_number=90,
        score=435,
        logged_at=RESET_BEFORE_THAT - timedelta(days=3),
    )

    post_due(connection, FakeClient(channel), POST_DUE_AT)

    description = sent_description(channel)
    assert "Nobody here logged yesterday's dive." in description
    assert "#90" not in description


def test_a_post_missed_past_the_grace_period_is_skipped_logged_and_moved_on(
    connection: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    channel = FakeChannel(channel_id=CHANNEL_ID)
    set_up_post(connection)
    late_now = POST_DUE_AT + daily.GRACE_PERIOD + timedelta(minutes=1)

    with caplog.at_level(logging.WARNING, logger="krillbot"):
        post_due(connection, FakeClient(channel), late_now)

    assert channel.sent_messages == []
    assert caplog.messages == [f"[10] Skipped the daily post due at {POST_DUE_AT.isoformat()}"]
    assert next_run_of(connection) == POST_DUE_AT + timedelta(days=1)


def test_a_failed_send_is_logged_and_still_moves_on_to_tomorrow(
    connection: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    send_error = discord.Forbidden(SimpleNamespace(status=403, reason="Forbidden"), "denied")
    set_up_post(connection)

    with caplog.at_level(logging.WARNING, logger="krillbot"):
        post_due(
            connection,
            FakeClient(FakeChannel(channel_id=CHANNEL_ID, send_error=send_error)),
            POST_DUE_AT,
        )

    assert caplog.messages == ["[10] Could not send the daily post: Forbidden 403"]
    assert next_run_of(connection) == POST_DUE_AT + timedelta(days=1)


def test_a_missing_channel_is_logged_and_still_moves_on_to_tomorrow(
    connection: sqlite3.Connection,
    caplog: pytest.LogCaptureFixture,
) -> None:
    set_up_post(connection)

    with caplog.at_level(logging.WARNING, logger="krillbot"):
        post_due(connection, FakeClient(), POST_DUE_AT)

    assert caplog.messages == [f"[10] Could not find channel {CHANNEL_ID} for the daily post"]
    assert next_run_of(connection) == POST_DUE_AT + timedelta(days=1)


def test_one_servers_failure_does_not_stop_anothers_post(
    connection: sqlite3.Connection,
) -> None:
    working_channel = FakeChannel(channel_id=301)
    set_up_post(connection, guild_id=10)
    set_up_post(connection, guild_id=11, channel_id=301)

    post_due(connection, FakeClient(working_channel), POST_DUE_AT)

    assert len(working_channel.sent_messages) == 1
    assert next_run_of(connection, guild_id=10) == POST_DUE_AT + timedelta(days=1)
    assert next_run_of(connection, guild_id=11) == POST_DUE_AT + timedelta(days=1)
