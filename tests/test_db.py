"""SQLite schema and version contract tests."""

from __future__ import annotations

import sqlite3

import pytest

from krillbot import db


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
