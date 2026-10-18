"""Every user-facing string and embed produced by Krill Bot."""

from __future__ import annotations

import discord

HELP_TITLE = "Krill Bot"
HELP_DESCRIPTION = (
    "An unofficial Discord companion for Krillion. Log daily results, compare "
    "server boards, and keep track of streaks. Krill Bot never contacts "
    "krillion.io."
)
GENERIC_ERROR_MESSAGE = "Something went wrong. Please try again."
PERMISSION_ERROR_MESSAGE = "You do not have permission to use that command."


def help_embed() -> discord.Embed:
    """Describe the bot without implying affiliation with Krillion."""
    return discord.Embed(title=HELP_TITLE, description=HELP_DESCRIPTION)
