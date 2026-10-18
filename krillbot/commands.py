"""Application commands registered by Krill Bot."""

from __future__ import annotations

import logging
import sqlite3
from datetime import UTC, datetime
from typing import Any, Literal

import discord
from discord import app_commands

from krillbot import config, db, embeds
from krillbot.boards import BoardPeriod, calculate_streak, compile_board
from krillbot.clock import next_occurrence, parse_clock
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
        embeds.daily_board_pages(current_daily_number, standings),
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
        embeds.period_board_pages(selected_period, standings),
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


# default_permissions only sets who sees /setup at first, and a server may widen it,
# so every subcommand also checks Manage Server when it is used.
setup_group = app_commands.Group(
    name="setup",
    description=embeds.SETUP_GROUP_DESCRIPTION,
    guild_only=True,
    default_permissions=discord.Permissions(manage_guild=True),
)


@setup_group.command(name="visibility", description=embeds.SETUP_VISIBILITY_DESCRIPTION)
@app_commands.describe(scores=embeds.SETUP_VISIBILITY_PARAMETER_DESCRIPTION)
@app_commands.checks.has_permissions(manage_guild=True)
async def setup_visibility_command(
    interaction: discord.Interaction,
    scores: Literal["hidden", "shown"],
) -> None:
    """Choose whether /dive today waits until the viewer has logged."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    hide_until_logged = scores == "hidden"
    db.set_hide_scores_until_logged(
        _database_connection(interaction),
        guild_id=guild_id,
        hide_until_logged=hide_until_logged,
    )
    await interaction.response.send_message(
        embeds.visibility_changed_message(hide_until_logged=hide_until_logged),
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )


@setup_group.command(name="show", description=embeds.SETUP_SHOW_DESCRIPTION)
@app_commands.checks.has_permissions(manage_guild=True)
async def setup_show_command(interaction: discord.Interaction) -> None:
    """Show this server's settings to the manager privately."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    connection = _database_connection(interaction)
    await interaction.response.send_message(
        embed=embeds.settings_embed(
            hide_until_logged=db.hide_scores_until_logged(connection, guild_id=guild_id),
            daily_post_summary=_daily_post_summary(connection, guild_id),
        ),
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )


def _daily_post_summary(connection: sqlite3.Connection, guild_id: int) -> str | None:
    daily_post = db.daily_post_setting(connection, guild_id=guild_id)
    if daily_post is None:
        return None
    return embeds.daily_post_summary(
        daily_post.channel_id,
        daily_post.clock,
        daily_post.reset_clock,
        default_post_clock=config.DAILY_POST_TIME,
        default_reset_clock=config.DAILY_RESET_TIME,
    )


# A subgroup takes guild_only and default_permissions from /setup; Discord sets
# them on top-level commands only.
daily_setup_group = app_commands.Group(
    name="daily",
    description=embeds.DAILY_SETUP_GROUP_DESCRIPTION,
    parent=setup_group,
)


@daily_setup_group.command(name="here", description=embeds.DAILY_HERE_DESCRIPTION)
@app_commands.describe(
    time=embeds.DAILY_HERE_TIME_DESCRIPTION,
    reset=embeds.DAILY_HERE_RESET_DESCRIPTION,
)
@app_commands.checks.has_permissions(manage_guild=True)
async def daily_here_command(
    interaction: discord.Interaction,
    time: str | None = None,
    reset: str | None = None,
) -> None:
    """Set up or move this server's daily post to the current channel or thread."""
    guild_id = interaction.guild_id
    channel_id = interaction.channel_id
    if guild_id is None or channel_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    # An omitted time is stored as unset, so the server follows the environment
    # fallback even if that changes later.
    post_clock = None if time is None else parse_clock(time)
    reset_clock = None if reset is None else parse_clock(reset)
    if (time is not None and post_clock is None) or (reset is not None and reset_clock is None):
        await interaction.response.send_message(
            embeds.CLOCK_UNREADABLE_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    connection = _database_connection(interaction)
    previous_channel_id = db.set_daily_post(
        connection,
        guild_id=guild_id,
        channel_id=channel_id,
        post_clock=post_clock,
        reset_clock=reset_clock,
        next_run=next_occurrence(
            post_clock or config.DAILY_POST_TIME,
            datetime.now(UTC),
            config.BOT_TIMEZONE,
        ),
    )
    LOGGER.info("[%s] Daily post set up in channel %s", guild_id, channel_id)
    summary = embeds.daily_post_summary(
        channel_id,
        post_clock,
        reset_clock,
        default_post_clock=config.DAILY_POST_TIME,
        default_reset_clock=config.DAILY_RESET_TIME,
    )
    await interaction.response.send_message(
        embeds.daily_post_set_message(summary, previous_channel_id=previous_channel_id),
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )


@daily_setup_group.command(name="stop", description=embeds.DAILY_STOP_DESCRIPTION)
@app_commands.checks.has_permissions(manage_guild=True)
async def daily_stop_command(interaction: discord.Interaction) -> None:
    """Stop this server's daily post; stopping twice is harmless."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    stopped = db.stop_daily_post(_database_connection(interaction), guild_id=guild_id)
    if stopped:
        LOGGER.info("[%s] Daily post stopped", guild_id)
    await interaction.response.send_message(
        embeds.DAILY_POST_STOPPED_MESSAGE if stopped else embeds.NO_DAILY_POST_TO_STOP_MESSAGE,
        ephemeral=True,
        allowed_mentions=NO_MENTIONS,
    )


@daily_setup_group.command(name="show", description=embeds.DAILY_SHOW_DESCRIPTION)
@app_commands.checks.has_permissions(manage_guild=True)
async def daily_show_command(interaction: discord.Interaction) -> None:
    """Show where and when this server's daily post goes."""
    guild_id = interaction.guild_id
    if guild_id is None:
        await interaction.response.send_message(
            embeds.SERVER_ONLY_MESSAGE, ephemeral=True, allowed_mentions=NO_MENTIONS
        )
        return
    await interaction.response.send_message(
        embeds.daily_post_show_message(
            _daily_post_summary(_database_connection(interaction), guild_id)
        ),
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


@app_commands.command(name="help", description=embeds.HELP_COMMAND_DESCRIPTION)
async def help_command(interaction: discord.Interaction) -> None:
    """Show the bot's purpose and unofficial status."""
    await interaction.response.send_message(embed=embeds.help_embed(), allowed_mentions=NO_MENTIONS)


APPLICATION_COMMANDS: tuple[Any, ...] = (dive_group, setup_group, help_command, log_message_command)
