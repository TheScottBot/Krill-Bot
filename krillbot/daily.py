"""The daily post: due times, yesterday's board, posting, and always moving on.

Each server has at most one daily post. The bot's loop calls post_due every
minute. A due post always moves on to its next day, even when posting fails, so
nothing is posted over and over; a post missed by more than the grace period,
because the bot was down, is skipped rather than posted late.
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Protocol

import discord

from krillbot import config, db, embeds
from krillbot.boards import BoardPeriod, BoardStanding, compile_board
from krillbot.clock import next_occurrence, previous_occurrence

LOGGER = logging.getLogger("krillbot")
NO_MENTIONS = discord.AllowedMentions.none()
# Later than this, a post would land well into the evening or the next day, so
# it is skipped rather than sent late.
GRACE_PERIOD = timedelta(hours=6)


class ChannelLookup(Protocol):
    """The part of the Discord client the daily post needs."""

    def get_channel(self, channel_id: int, /) -> Any: ...


def yesterday_window(reset_clock: str, now: datetime) -> tuple[datetime, datetime]:
    """Return the UTC start and end of the dive before the one open now."""
    window_end = previous_occurrence(reset_clock, now, config.BOT_TIMEZONE)
    # One microsecond earlier lands inside the previous dive, so its own reset is
    # found even on a day that summer time makes 23 or 25 hours long.
    window_start = previous_occurrence(
        reset_clock, window_end - timedelta(microseconds=1), config.BOT_TIMEZONE
    )
    return window_start, window_end


def yesterday_board(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
    reset_clock: str,
    now: datetime,
) -> tuple[int | None, list[BoardStanding]]:
    """Return yesterday's daily number in one server and its standings."""
    window_start, window_end = yesterday_window(reset_clock, now)
    logged_numbers = db.daily_numbers_logged_between(
        connection,
        guild_id=guild_id,
        start=window_start,
        end=window_end,
    )
    if not logged_numbers:
        return None, []
    # Late logs of an older dive can land in the window, so the newest number
    # logged there is yesterday's.
    yesterday_number = max(logged_numbers)
    entries = [
        entry
        for entry in db.server_board_entries(connection, guild_id=guild_id)
        if entry.daily_number == yesterday_number
    ]
    return yesterday_number, compile_board(
        entries, BoardPeriod.ALL, current_daily_number=yesterday_number
    )


async def _send_daily_post(
    client: ChannelLookup,
    connection: sqlite3.Connection,
    schedule: db.DailyPostSchedule,
    now: datetime,
) -> None:
    if now - schedule.next_run > GRACE_PERIOD:
        LOGGER.warning(
            "[%s] Skipped the daily post due at %s",
            schedule.guild_id,
            schedule.next_run.isoformat(),
        )
        return
    channel = client.get_channel(schedule.channel_id)
    if channel is None or not hasattr(channel, "send"):
        LOGGER.warning(
            "[%s] Could not find channel %s for the daily post",
            schedule.guild_id,
            schedule.channel_id,
        )
        return
    yesterday_number, standings = yesterday_board(
        connection,
        guild_id=schedule.guild_id,
        reset_clock=schedule.reset_clock or config.DAILY_RESET_TIME,
        now=now,
    )
    # Yesterday's dive is over for everyone, so the post shows its scores even
    # where /dive today hides the current dive's.
    await channel.send(
        embed=embeds.daily_post_embed(yesterday_number, standings),
        allowed_mentions=NO_MENTIONS,
    )
    LOGGER.info("[%s] Sent the daily post", schedule.guild_id)


async def post_due(client: ChannelLookup, connection: sqlite3.Connection, now: datetime) -> None:
    """Send every due daily post, then move each on to its next day."""
    for schedule in db.daily_posts_due(connection, now=now):
        try:
            await _send_daily_post(client, connection, schedule, now)
        except discord.HTTPException as error:
            LOGGER.warning(
                "[%s] Could not send the daily post: %s %s",
                schedule.guild_id,
                type(error).__name__,
                error.status,
            )
        except Exception:
            # One server's unexpected failure must not stop the loop for the rest.
            LOGGER.exception("[%s] The daily post failed", schedule.guild_id)
        finally:
            # Always on to the next day, so a failure cannot post it over and over.
            db.move_daily_post_on(
                connection,
                guild_id=schedule.guild_id,
                next_run=next_occurrence(
                    schedule.post_clock or config.DAILY_POST_TIME,
                    now,
                    config.BOT_TIMEZONE,
                ),
            )
