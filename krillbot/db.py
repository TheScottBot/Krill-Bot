"""Versioned SQLite schema and repository operations."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime

from krillbot.result_grammar import ParsedResult

SCHEMA_VERSION = 1

SCHEMA_STATEMENTS = (
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
        for statement in SCHEMA_STATEMENTS:
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
