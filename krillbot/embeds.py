"""Every user-facing string and embed produced by Krill Bot."""

from __future__ import annotations

import discord

from krillbot.boards import BoardStanding, Streak

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
TODAY_COMMAND_DESCRIPTION = "Show the latest daily board for this server"
BOARD_COMMAND_DESCRIPTION = "Show a rolling server board"
BOARD_PERIOD_DESCRIPTION = "Choose week, month, or all"
STREAK_COMMAND_DESCRIPTION = "Show current and longest streaks"
TODAY_HIDDEN_MESSAGE = "Today's scores are hidden until you log your own result."
NO_BOARD_RESULTS_MESSAGE = "No results have been logged in this server yet."
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


def board_pages(title: str, standings: list[BoardStanding]) -> list[discord.Embed]:
    """Format standings as bounded pages of twenty rows."""
    page_size = 20
    pages: list[discord.Embed] = []
    for page_start in range(0, len(standings), page_size):
        page_standings = standings[page_start : page_start + page_size]
        lines = [
            f"{page_start + position}. <@{standing.user_id}>: {standing.total} total, "
            f"{standing.dives} dives, {standing.average:.1f} average, {standing.best} best"
            for position, standing in enumerate(page_standings, start=1)
        ]
        pages.append(discord.Embed(title=title, description="\n".join(lines)))
    return pages


def streak_message(streak: Streak, *, own_streak: bool) -> str:
    """Format current and longest streak counts."""
    subject = "Your" if own_streak else "Their"
    return (
        f"{subject} current streak is {streak.current}; "
        f"{subject.lower()} longest is {streak.longest}."
    )
