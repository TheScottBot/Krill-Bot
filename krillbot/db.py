"""Versioned SQLite schema and repository operations."""

from __future__ import annotations

import sqlite3

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
