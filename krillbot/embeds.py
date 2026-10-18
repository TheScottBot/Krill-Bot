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
SERVER_ONLY_MESSAGE = "This command can only be used in a server."
OWN_MESSAGE_ONLY_MESSAGE = "You can only log a result from your own message."
NO_RESULTS_MESSAGE = "You have not logged any results in this server."
LOG_MESSAGE_COMMAND_NAME = "Log Krillion result"
DIVE_GROUP_DESCRIPTION = "Log and review Krillion daily results"
LOG_COMMAND_DESCRIPTION = "Log a copied Krillion daily result"
LOG_RESULT_PARAMETER_DESCRIPTION = "The text from Krillion's Copy result button"
ME_COMMAND_DESCRIPTION = "Show your results from this server"
REJECTION_MESSAGES = {
    "too-long": "That's longer than any message with a Krillion result in it.",
    "not-a-result": (
        "this doesn't look like a result, feel free to message me on Discord to update the bot "
        "if its outdated."
    ),
    "several-results": "That has more than one result in it; log them one at a time.",
}


def help_embed() -> discord.Embed:
    """Describe the bot without implying affiliation with Krillion."""
    return discord.Embed(title=HELP_TITLE, description=HELP_DESCRIPTION)


def logged_result_message(daily_number: int, score: int, *, replaced: bool) -> str:
    """Confirm a newly stored or replaced result."""
    action = "Replaced" if replaced else "Logged"
    return f"{action} daily #{daily_number} with {score} points."


def rejection_message(reason: str) -> str:
    """Return the stable player-facing copy for a parser rejection."""
    return REJECTION_MESSAGES[reason]


def user_results_message(results: list[tuple[int, int, str]]) -> str:
    """Format one user's server-scoped result history."""
    if not results:
        return NO_RESULTS_MESSAGE
    lines = [
        f"#{daily_number}: {score} points {emoji_row}" for daily_number, score, emoji_row in results
    ]
    return "Your Krillion results in this server:\n" + "\n".join(lines)
