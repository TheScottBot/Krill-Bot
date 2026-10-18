"""Versioned SQLite schema and repository operations."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from krillbot.boards import BoardEntry
from krillbot.result_grammar import ParsedResult

SCHEMA_VERSION = 2

# The first schema is kept verbatim so a new database follows the same upgrade
# path as an old one, and every upgrade is exercised on every fresh start.
SCHEMA_VERSION_1_STATEMENTS = (
    """
    CREATE TABLE daily_results (
        guild_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        daily_number INTEGER NOT NULL,
        score INTEGER NOT NULL,
        emoji_row TEXT NOT NULL,
        logged_at TEXT NOT NULL,
        PRIMARY KEY (guild_id, user_id, daily_number)
    )
    """,
    """
    CREATE TABLE daily_posts (
        guild_id INTEGER PRIMARY KEY,
        channel_id INTEGER NOT NULL,
        clock TEXT NOT NULL,
        next_run TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE guild_settings (
        guild_id INTEGER PRIMARY KEY,
        hide_until_logged INTEGER NOT NULL
    )
    """,
)

# Version 2 lets a server leave its post and reset times unset, so it follows
# the environment fallbacks if they change, and stores the server's reset time.
# SQLite cannot drop a NOT NULL constraint in place, so the table is rebuilt.
SCHEMA_UPGRADE_STATEMENTS = {
    2: (
        """
        CREATE TABLE daily_posts_version_2 (
            guild_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            clock TEXT,
            reset_clock TEXT,
            next_run TEXT NOT NULL
        )
        """,
        """
        INSERT INTO daily_posts_version_2 (guild_id, channel_id, clock, reset_clock, next_run)
        SELECT guild_id, channel_id, clock, NULL, next_run FROM daily_posts
        """,
        "DROP TABLE daily_posts",
        "ALTER TABLE daily_posts_version_2 RENAME TO daily_posts",
    ),
}


class NewerSchemaError(RuntimeError):
    """The database belongs to a newer Krill Bot version."""


@dataclass(frozen=True, slots=True)
class StoredDailyResult:
    """A permitted result row returned by a server-scoped query."""

    daily_number: int
    score: int
    emoji_row: str
    logged_at: str


def initialise(database_path: str) -> sqlite3.Connection:
    """Open a database and bring an older schema up to the current version."""
    connection = sqlite3.connect(database_path)
    try:
        initialise_connection(connection)
    except Exception:
        connection.close()
        raise
    return connection


def initialise_connection(connection: sqlite3.Connection) -> None:
    """Validate or initialise an already-open database connection."""
    current_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if current_version > SCHEMA_VERSION:
        raise NewerSchemaError(
            f"Database schema {current_version} is newer than supported schema {SCHEMA_VERSION}"
        )
    if current_version == SCHEMA_VERSION:
        return

    with connection:
        if current_version == 0:
            for statement in SCHEMA_VERSION_1_STATEMENTS:
                connection.execute(statement)
            current_version = 1
        for target_version in range(current_version + 1, SCHEMA_VERSION + 1):
            for statement in SCHEMA_UPGRADE_STATEMENTS[target_version]:
                connection.execute(statement)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


def store_daily_result(
    connection: sqlite3.Connection,
    guild_id: int,
    user_id: int,
    parsed_result: ParsedResult,
    logged_at: datetime,
) -> bool:
    """Insert or replace one result and report whether a row was replaced."""
    with connection:
        existing_row = connection.execute(
            """
            SELECT 1
            FROM daily_results
            WHERE guild_id = ? AND user_id = ? AND daily_number = ?
            """,
            (guild_id, user_id, parsed_result.daily_number),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO daily_results (
                guild_id, user_id, daily_number, score, emoji_row, logged_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (guild_id, user_id, daily_number) DO UPDATE SET
                score = excluded.score,
                emoji_row = excluded.emoji_row,
                logged_at = excluded.logged_at
            """,
            (
                guild_id,
                user_id,
                parsed_result.daily_number,
                parsed_result.score,
                parsed_result.emoji_row,
                logged_at.isoformat(),
            ),
        )
    return existing_row is not None


def user_results(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
    user_id: int,
) -> list[StoredDailyResult]:
    """Return one user's results from one server, newest daily number first."""
    rows = connection.execute(
        """
        SELECT daily_number, score, emoji_row, logged_at
        FROM daily_results
        WHERE guild_id = ? AND user_id = ?
        ORDER BY daily_number DESC
        """,
        (guild_id, user_id),
    ).fetchall()
    return [StoredDailyResult(*row) for row in rows]


def server_board_entries(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
) -> list[BoardEntry]:
    """Return the score fields for one server only."""
    rows = connection.execute(
        """
        SELECT user_id, daily_number, score
        FROM daily_results
        WHERE guild_id = ?
        """,
        (guild_id,),
    ).fetchall()
    return [BoardEntry(*row) for row in rows]


def latest_daily_number(connection: sqlite3.Connection, *, guild_id: int) -> int | None:
    """Return the highest daily number logged in one server."""
    row = connection.execute(
        "SELECT MAX(daily_number) FROM daily_results WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()
    daily_number = row[0]
    return None if daily_number is None else int(daily_number)


def hide_scores_until_logged(connection: sqlite3.Connection, *, guild_id: int) -> bool:
    """Return the server setting, defaulting to hidden scores."""
    row = connection.execute(
        "SELECT hide_until_logged FROM guild_settings WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()
    return True if row is None else bool(row[0])


def user_has_daily_result(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
    user_id: int,
    daily_number: int,
) -> bool:
    """Return whether one user logged one daily result in one server."""
    row = connection.execute(
        """
        SELECT 1 FROM daily_results
        WHERE guild_id = ? AND user_id = ? AND daily_number = ?
        """,
        (guild_id, user_id, daily_number),
    ).fetchone()
    return row is not None


def user_daily_numbers(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
    user_id: int,
) -> list[int]:
    """Return one user's daily numbers from one server."""
    rows = connection.execute(
        """
        SELECT daily_number FROM daily_results
        WHERE guild_id = ? AND user_id = ?
        ORDER BY daily_number
        """,
        (guild_id, user_id),
    ).fetchall()
    return [row[0] for row in rows]


@dataclass(frozen=True, slots=True)
class DailyPostSetting:
    """Where and when one server's daily post is sent."""

    channel_id: int
    clock: str | None
    reset_clock: str | None = None


@dataclass(frozen=True, slots=True)
class DailyPostSchedule:
    """A server's daily post as the posting loop needs it."""

    guild_id: int
    channel_id: int
    post_clock: str | None
    reset_clock: str | None
    next_run: datetime


def set_hide_scores_until_logged(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
    hide_until_logged: bool,
) -> None:
    """Store one server's visibility choice; repeating it changes nothing further."""
    with connection:
        connection.execute(
            """
            INSERT INTO guild_settings (guild_id, hide_until_logged) VALUES (?, ?)
            ON CONFLICT (guild_id) DO UPDATE SET hide_until_logged = excluded.hide_until_logged
            """,
            (guild_id, int(hide_until_logged)),
        )


def daily_post_setting(connection: sqlite3.Connection, *, guild_id: int) -> DailyPostSetting | None:
    """Return one server's daily post, or nothing when it has not set one up."""
    row = connection.execute(
        "SELECT channel_id, clock, reset_clock FROM daily_posts WHERE guild_id = ?",
        (guild_id,),
    ).fetchone()
    return None if row is None else DailyPostSetting(*row)


def set_daily_post(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
    channel_id: int,
    post_clock: str | None,
    reset_clock: str | None,
    next_run: datetime,
) -> int | None:
    """Set up or move one server's daily post, returning the channel it left."""
    with connection:
        previous_row = connection.execute(
            "SELECT channel_id FROM daily_posts WHERE guild_id = ?",
            (guild_id,),
        ).fetchone()
        connection.execute(
            """
            INSERT INTO daily_posts (guild_id, channel_id, clock, reset_clock, next_run)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (guild_id) DO UPDATE SET
                channel_id = excluded.channel_id,
                clock = excluded.clock,
                reset_clock = excluded.reset_clock,
                next_run = excluded.next_run
            """,
            (guild_id, channel_id, post_clock, reset_clock, next_run.isoformat()),
        )
    if previous_row is None or previous_row[0] == channel_id:
        return None
    return int(previous_row[0])


def stop_daily_post(connection: sqlite3.Connection, *, guild_id: int) -> bool:
    """Stop one server's daily post, reporting whether there was one to stop."""
    with connection:
        cursor = connection.execute("DELETE FROM daily_posts WHERE guild_id = ?", (guild_id,))
    return cursor.rowcount > 0


def daily_posts_due(connection: sqlite3.Connection, *, now: datetime) -> list[DailyPostSchedule]:
    """Return every daily post whose next run has arrived, oldest first."""
    rows = connection.execute(
        "SELECT guild_id, channel_id, clock, reset_clock, next_run FROM daily_posts"
    ).fetchall()
    schedules = [
        DailyPostSchedule(
            guild_id=guild_id,
            channel_id=channel_id,
            post_clock=post_clock,
            reset_clock=reset_clock,
            next_run=datetime.fromisoformat(next_run),
        )
        for guild_id, channel_id, post_clock, reset_clock, next_run in rows
    ]
    return sorted(
        (schedule for schedule in schedules if schedule.next_run <= now),
        key=lambda schedule: (schedule.next_run, schedule.guild_id),
    )


def move_daily_post_on(
    connection: sqlite3.Connection, *, guild_id: int, next_run: datetime
) -> None:
    """Record one server's next daily post time."""
    with connection:
        connection.execute(
            "UPDATE daily_posts SET next_run = ? WHERE guild_id = ?",
            (next_run.isoformat(), guild_id),
        )


def daily_numbers_logged_between(
    connection: sqlite3.Connection,
    *,
    guild_id: int,
    start: datetime,
    end: datetime,
) -> set[int]:
    """Return one server's daily numbers logged at or after start and before end."""
    rows = connection.execute(
        "SELECT daily_number, logged_at FROM daily_results WHERE guild_id = ?",
        (guild_id,),
    ).fetchall()
    # Compared as instants rather than text, because isoformat omits zero microseconds.
    return {
        daily_number
        for daily_number, logged_at in rows
        if start <= datetime.fromisoformat(logged_at) < end
    }
