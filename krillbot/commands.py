"""Application commands registered by Krill Bot."""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from typing import Any, Literal

import discord
from discord import app_commands

from krillbot import db, embeds
from krillbot.boards import BoardPeriod, calculate_streak, compile_board
from krillbot.result_grammar import ParsedResult, ParseRejection, parse_daily_result

NO_MENTIONS = discord.AllowedMentions.none()
LOGGER = logging.getLogger("krillbot")


def _database_connection(interaction: discord.Interaction) -> sqlite3.Connection:
    connection = getattr(interaction.client, "database_connection", None)
    if not isinstance(connection, sqlite3.Connection):
        raise RuntimeError("Discord client has no database connection")
    return connection


async def _store_supplied_result(interaction: discord.Interaction, supplied_text: str) -> None:
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE,
            ephemeral=True,
            allowed_mentions=NO_MENTIONS,
        )
        return

    parse_outcome = parse_daily_result(supplied_text)
    if isinstance(parse_outcome, ParseRejection):
        LOGGER.info("[%s] Refused result: %s", guild_id, parse_outcome.value)
        await interaction.response.send_message(
            embeds.rejection_message(parse_outcome.value),
            ephemeral=True,
            allowed_mentions=NO_MENTIONS,
        )
        return

    parsed_result: ParsedResult = parse_outcome
    replaced = db.store_daily_result(
        _database_connection(interaction),
        guild_id,
        interaction.user.id,
        parsed_result,
        datetime.now(UTC),
    )
    if not parsed_result.score_matches_known_points:
        LOGGER.info("[%s] Accepted result with an unverified score", guild_id)
    await interaction.response.send_message(
        embeds.logged_result_message(
            parsed_result.daily_number,
            parsed_result.score,
            replaced=replaced,
        ),
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )


dive_group = app_commands.Group(name="dive", description=embeds.DIVE_GROUP_DESCRIPTION)


@dive_group.command(name="log", description=embeds.LOG_COMMAND_DESCRIPTION)
@app_commands.describe(result=embeds.LOG_RESULT_PARAMETER_DESCRIPTION)
async def log_result_command(interaction: discord.Interaction, result: str) -> None:
    """Parse and store one caller-supplied daily result."""
    await _store_supplied_result(interaction, result)


@dive_group.command(name="me", description=embeds.ME_COMMAND_DESCRIPTION)
async def me_command(interaction: discord.Interaction) -> None:
    """Show the caller's results from the current server only."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE,
            ephemeral=True,
            allowed_mentions=NO_MENTIONS,
        )
        return
    stored_results = db.user_results(
        _database_connection(interaction),
        guild_id=guild_id,
        user_id=interaction.user.id,
    )
    response_text = embeds.user_results_message(
        [(result.daily_number, result.score, result.emoji_row) for result in stored_results]
    )
    await interaction.response.send_message(
        response_text,
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )


async def _send_board_pages(
    interaction: discord.Interaction,
    pages: list[discord.Embed],
) -> None:
    if not pages:
        await interaction.response.send_message(
            embeds.NO_BOARD_RESULTS_MESSAGE,
            ephemeral=True,
            allowed_mentions=NO_MENTIONS,
        )
        return
    await interaction.response.send_message(
        embed=pages[0],
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )
    for page in pages[1:]:
        await interaction.followup.send(
            embed=page,
            ephemeral=True,
            allowed_mentions=NO_MENTIONS,
        )


@dive_group.command(name="today", description=embeds.TODAY_COMMAND_DESCRIPTION)
async def today_command(interaction: discord.Interaction) -> None:
    """Show the latest logged daily board subject to server visibility."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    connection = _database_connection(interaction)
    current_daily_number = db.latest_daily_number(connection, guild_id=guild_id)
    if current_daily_number is None:
        await _send_board_pages(interaction, [])
        return
    if db.hide_scores_until_logged(connection, guild_id=guild_id) and not db.user_has_daily_result(
        connection,
        guild_id=guild_id,
        user_id=interaction.user.id,
        daily_number=current_daily_number,
    ):
        await interaction.response.send_message(
            embeds.TODAY_HIDDEN_MESSAGE,
            ephemeral=True,
            allowed_mentions=NO_MENTIONS,
        )
        return
    entries = [
        entry
        for entry in db.server_board_entries(connection, guild_id=guild_id)
        if entry.daily_number == current_daily_number
    ]
    standings = compile_board(entries, BoardPeriod.ALL, current_daily_number=current_daily_number)
    await _send_board_pages(
        interaction,
        embeds.board_pages(f"Daily #{current_daily_number}", standings),
    )


@dive_group.command(name="board", description=embeds.BOARD_COMMAND_DESCRIPTION)
@app_commands.describe(period=embeds.BOARD_PERIOD_DESCRIPTION)
async def board_command(
    interaction: discord.Interaction,
    period: Literal["week", "month", "all"],
) -> None:
    """Show a rolling aggregate board for the current server."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    connection = _database_connection(interaction)
    current_daily_number = db.latest_daily_number(connection, guild_id=guild_id)
    if current_daily_number is None:
        await _send_board_pages(interaction, [])
        return
    selected_period = BoardPeriod(period)
    standings = compile_board(
        db.server_board_entries(connection, guild_id=guild_id),
        selected_period,
        current_daily_number=current_daily_number,
    )
    await _send_board_pages(
        interaction,
        embeds.board_pages(f"{selected_period.value.title()} board", standings),
    )


@dive_group.command(name="streak", description=embeds.STREAK_COMMAND_DESCRIPTION)
async def streak_command(
    interaction: discord.Interaction,
    player: discord.Member | None = None,
) -> None:
    """Show a player's server-scoped current and longest streaks."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    connection = _database_connection(interaction)
    current_daily_number = db.latest_daily_number(connection, guild_id=guild_id)
    target_user_id = interaction.user.id if player is None else player.id
    streak = calculate_streak(
        db.user_daily_numbers(connection, guild_id=guild_id, user_id=target_user_id),
        current_daily_number=current_daily_number or 0,
    )
    await interaction.response.send_message(
        embeds.streak_message(streak, own_streak=target_user_id == interaction.user.id),
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )


@app_commands.context_menu(name=embeds.LOG_MESSAGE_COMMAND_NAME)
async def log_message_command(
    interaction: discord.Interaction,
    message: discord.Message,
) -> None:
    """Log a result only from a message written by the caller."""
    if message.author.id != interaction.user.id:
        await interaction.response.send_message(
            embeds.OWN_MESSAGE_ONLY_MESSAGE,
            ephemeral=True,
            allowed_mentions=NO_MENTIONS,
        )
        return
    await _store_supplied_result(interaction, message.content)


@app_commands.command(name="help", description="Show what Krill Bot does")
async def help_command(interaction: discord.Interaction) -> None:
    """Show the bot's purpose and unofficial status."""
    await interaction.response.send_message(embed=embeds.help_embed(), allowed_mentions=NO_MENTIONS)


APPLICATION_COMMANDS: tuple[Any, ...] = (dive_group, help_command, log_message_command)
