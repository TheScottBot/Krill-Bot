"""Discord client construction and lifecycle."""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, cast

import discord
from discord import app_commands
from discord.ext import tasks

from krillbot import config, daily, db, embeds
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

    @tasks.loop(minutes=1)
    async def daily_loop(self) -> None:
        """Send every daily post that has come due."""
        if self.database_connection is None:
            return
        await daily.post_due(self, self.database_connection, datetime.now(UTC))

    async def on_ready(self) -> None:
        """Start the daily loop once the gateway is ready.

        Started here rather than in setup_hook, as ProcBot does, so the loop only
        runs against a ready client and setup_hook stays free of background
        tasks. Ready fires again after a reconnect, hence the guard.
        """
        if not self.daily_loop.is_running():
            self.daily_loop.start()

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        """Forget everything a server owns once the bot is removed from it."""
        if self.database_connection is None:
            return
        db.forget_guild(
            self.database_connection,
            guild_id=guild.id,
            origin=db.DeletionOrigin.GUILD_REMOVED,
        )

    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Stop a daily post whose channel no longer exists."""
        if self.database_connection is None:
            return
        db.stop_daily_posts_in_channel(
            self.database_connection,
            guild_id=channel.guild.id,
            channel_id=channel.id,
            origin=db.DeletionOrigin.CHANNEL_DELETED,
        )

    async def on_raw_thread_delete(self, payload: discord.RawThreadDeleteEvent) -> None:
        """Stop a daily post whose thread no longer exists.

        The raw event fires even for threads missing from the cache, which an
        idle thread holding only a daily post usually is.
        """
        if self.database_connection is None:
            return
        db.stop_daily_posts_in_channel(
            self.database_connection,
            guild_id=payload.guild_id,
            channel_id=payload.thread_id,
            origin=db.DeletionOrigin.CHANNEL_DELETED,
        )

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
