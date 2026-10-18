"""Every user-facing string and embed produced by Krill Bot."""

from __future__ import annotations

import discord

from krillbot.boards import BoardPeriod, BoardStanding, Streak
from krillbot.result_grammar import bearing_for_score

DISCORD_MESSAGE_CONTENT_LIMIT = 2_000
DISCORD_EMBED_DESCRIPTION_LIMIT = 4_096
BOARD_PAGE_SIZE = 20
TRUNCATION_NOTE = "(truncated to fit Discord's limits)"

HELP_TITLE = "Krill Bot"
HELP_COMMAND_DESCRIPTION = "Show what Krill Bot does"
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
PERIOD_BOARD_TITLES = {
    BoardPeriod.WEEK: "Week board",
    BoardPeriod.MONTH: "Month board",
    BoardPeriod.ALL: "All-time board",
}
SETUP_GROUP_DESCRIPTION = "Choose how Krill Bot behaves in this server"
SETUP_VISIBILITY_DESCRIPTION = "Choose whether today's scores wait until a viewer has logged"
SETUP_VISIBILITY_PARAMETER_DESCRIPTION = "hidden until each viewer logs, or shown to everyone"
SETUP_SHOW_DESCRIPTION = "Show this server's Krill Bot settings"
SETTINGS_TITLE = "Krill Bot settings"
TODAY_SCORES_FIELD_NAME = "Today's scores"
DAILY_POST_FIELD_NAME = "Daily post"
SCORES_HIDDEN_SETTING = "Hidden until each viewer logs their own result"
SCORES_SHOWN_SETTING = "Shown to everyone"
DAILY_POST_NOT_SET_UP = "Not set up"
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


def _discord_length(text: str) -> int:
    """Measure in UTF-16 code units, which is never fewer than Discord's count.

    Discord's documentation gives its limits in characters without saying how an
    emoji is counted, so the larger measure keeps every reply under the limit.
    """
    return len(text.encode("utf-16-le")) // 2


def _truncated_line(line_text: str, limit: int) -> str:
    """Shorten one line to the limit, ending it with the truncation note."""
    if _discord_length(line_text) <= limit:
        return line_text
    suffix = " " + TRUNCATION_NOTE
    shortened_text = line_text[: limit - len(suffix)]
    while _discord_length(shortened_text + suffix) > limit:
        shortened_text = shortened_text[:-1]
    return shortened_text + suffix


def user_results_message(results: list[tuple[int, int, str]]) -> str:
    """Format one user's server-scoped history, newest first, inside the content limit."""
    if not results:
        return NO_RESULTS_MESSAGE
    header = "Your Krillion results in this server:"
    lines = [
        f"#{daily_number}: {score} points {emoji_row}" for daily_number, score, emoji_row in results
    ]
    complete_text = "\n".join([header, *lines])
    if _discord_length(complete_text) <= DISCORD_MESSAGE_CONTENT_LIMIT:
        return complete_text

    # Oldest results are dropped first, because the newest are the ones a player checks.
    kept_lines: list[str] = []
    kept_length = _discord_length(header) + 1 + _discord_length(TRUNCATION_NOTE)
    for line_text in lines:
        line_length = _discord_length(line_text) + 1
        if kept_length + line_length > DISCORD_MESSAGE_CONTENT_LIMIT:
            break
        kept_lines.append(line_text)
        kept_length += line_length
    return "\n".join([header, *kept_lines, TRUNCATION_NOTE])


def _board_pages(title: str, lines: list[str]) -> list[discord.Embed]:
    """Page board lines by row count and by Discord's description limit."""
    pages: list[discord.Embed] = []
    page_lines: list[str] = []
    page_length = 0
    for line_text in lines:
        bounded_line = _truncated_line(line_text, DISCORD_EMBED_DESCRIPTION_LIMIT)
        line_length = _discord_length(bounded_line)
        separator_length = 1 if page_lines else 0
        if page_lines and (
            len(page_lines) == BOARD_PAGE_SIZE
            or page_length + separator_length + line_length > DISCORD_EMBED_DESCRIPTION_LIMIT
        ):
            pages.append(discord.Embed(title=title, description="\n".join(page_lines)))
            page_lines = []
            page_length = 0
            separator_length = 0
        page_lines.append(bounded_line)
        page_length += separator_length + line_length
    if page_lines:
        pages.append(discord.Embed(title=title, description="\n".join(page_lines)))
    return pages


def daily_board_pages(daily_number: int, standings: list[BoardStanding]) -> list[discord.Embed]:
    """Format one daily number's scores, each with its published bearing."""
    lines = [
        f"{position}. <@{standing.user_id}>: {standing.best} points, "
        f"{bearing_for_score(standing.best).name}"
        for position, standing in enumerate(standings, start=1)
    ]
    return _board_pages(f"Daily #{daily_number}", lines)


def period_board_pages(period: BoardPeriod, standings: list[BoardStanding]) -> list[discord.Embed]:
    """Format a rolling board with dives, total, average, and best per player."""
    lines = [
        f"{position}. <@{standing.user_id}>: {standing.total} total, "
        f"{standing.dives} dives, {standing.average:.1f} average, {standing.best} best"
        for position, standing in enumerate(standings, start=1)
    ]
    return _board_pages(PERIOD_BOARD_TITLES[period], lines)


def visibility_changed_message(*, hide_until_logged: bool) -> str:
    """Confirm a server's new visibility choice to the manager who made it."""
    if hide_until_logged:
        return "Scores on /dive today are now hidden until each viewer logs their own result."
    return "Scores on /dive today are now shown to everyone in this server."


def settings_embed(
    *,
    hide_until_logged: bool,
    daily_post_channel_id: int | None,
    daily_post_clock: str | None,
) -> discord.Embed:
    """Describe one server's settings; a channel mention never pings anyone."""
    settings = discord.Embed(title=SETTINGS_TITLE)
    settings.add_field(
        name=TODAY_SCORES_FIELD_NAME,
        value=SCORES_HIDDEN_SETTING if hide_until_logged else SCORES_SHOWN_SETTING,
        inline=False,
    )
    if daily_post_channel_id is None or daily_post_clock is None:
        daily_post_text = DAILY_POST_NOT_SET_UP
    else:
        daily_post_text = f"<#{daily_post_channel_id}> at {daily_post_clock}"
    settings.add_field(name=DAILY_POST_FIELD_NAME, value=daily_post_text, inline=False)
    return settings


def streak_message(streak: Streak, *, own_streak: bool) -> str:
    """Format current and longest streak counts."""
    subject = "Your" if own_streak else "Their"
    return (
        f"{subject} current streak is {streak.current}; "
        f"{subject.lower()} longest is {streak.longest}."
    )
