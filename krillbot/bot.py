"""Discord client construction and lifecycle."""

from __future__ import annotations

import logging
import sqlite3
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, cast

import discord
from discord import app_commands

from krillbot import config, db, embeds
from krillbot.commands import APPLICATION_COMMANDS, NO_MENTIONS

LOGGER = logging.getLogger("krillbot")
LOG_FORMAT = "[{asctime}] [{levelname:<7}] {name}: {message}"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def build_file_log_handler(log_path: Path) -> RotatingFileHandler:
    """Create the rotating UTF-8 log after ensuring its directory exists."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return RotatingFileHandler(
        log_path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )


def setup_logging() -> None:
    """Log to the terminal and to a rotating file."""
    formatter = logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT, style="{")
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    try:
        file_handler = build_file_log_handler(config.LOG_PATH)
    except OSError as error:
        LOGGER.warning("Could not open the log file; using the terminal only: %s", error)
        return
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)


class KrillBot(discord.Client):
    """A slash-command client that does not consume privileged message events."""

    def __init__(self, database_connection: sqlite3.Connection | None = None) -> None:
        super().__init__(intents=discord.Intents.default())
        self.database_connection = database_connection
        self.tree = app_commands.CommandTree(self)
        for application_command in APPLICATION_COMMANDS:
            self.tree.add_command(application_command)
        # discord.py installs this callback by assignment, although its type stub
        # exposes on_error as a method and therefore rejects that documented pattern.
        command_tree_with_assignable_callback = cast(Any, self.tree)
        command_tree_with_assignable_callback.on_error = self.on_app_command_error

    async def setup_hook(self) -> None:
        """Register commands immediately in development servers or globally."""
        if not config.GUILD_IDS:
            synchronised_commands = await self.tree.sync()
            LOGGER.info("Synchronised %d global commands", len(synchronised_commands))
            return

        for guild_id in config.GUILD_IDS:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            try:
                synchronised_commands = await self.tree.sync(guild=guild)
            except discord.Forbidden:
                LOGGER.warning("Could not synchronise commands in server %s", guild_id)
                continue
            LOGGER.info(
                "Synchronised %d commands in server %s",
                len(synchronised_commands),
                guild_id,
            )

    async def on_app_command_completion(
        self,
        interaction: discord.Interaction,
        command: app_commands.Command[Any, ..., Any] | app_commands.ContextMenu,
    ) -> None:
        """Record only the command and server, never the user or submitted text."""
        LOGGER.info("[%s] /%s", interaction.guild_id or "DM", command.qualified_name)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ) -> None:
        """Reply privately to every command failure and retain its traceback."""
        command_name = interaction.command.qualified_name if interaction.command else "unknown"
        if isinstance(error, app_commands.CheckFailure):
            response_text = embeds.PERMISSION_ERROR_MESSAGE
        else:
            LOGGER.exception("/%s failed", command_name, exc_info=error)
            response_text = embeds.GENERIC_ERROR_MESSAGE

        if interaction.response.is_done():
            await interaction.followup.send(
                response_text,
                ephemeral=True,
                allowed_mentions=NO_MENTIONS,
            )
        else:
            await interaction.response.send_message(
                response_text,
                ephemeral=True,
                allowed_mentions=NO_MENTIONS,
            )


def main() -> None:
    """Initialise storage and start the Discord client."""
    setup_logging()
    connection = db.initialise(str(config.DATABASE_PATH))
    try:
        KrillBot(connection).run(config.DISCORD_TOKEN, log_handler=None)
    finally:
        connection.close()
