"""Application commands registered by Krill Bot."""

from __future__ import annotations

from typing import Any

import discord
from discord import app_commands

from krillbot import embeds

NO_MENTIONS = discord.AllowedMentions.none()


@app_commands.command(name="help", description="Show what Krill Bot does")
async def help_command(interaction: discord.Interaction) -> None:
    """Show the bot's purpose and unofficial status."""
    await interaction.response.send_message(embed=embeds.help_embed(), allowed_mentions=NO_MENTIONS)


APPLICATION_COMMANDS: tuple[app_commands.Command[Any, ..., None], ...] = (help_command,)
