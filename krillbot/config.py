"""Validated settings loaded from the repository environment file."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from krillbot.clock import parse_clock

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEVELOPMENT_MODE = "--dev" in sys.argv
ENVIRONMENT_FILE_NAME = ".env.dev" if DEVELOPMENT_MODE else ".env"

if not os.getenv("KRILLBOT_NO_DOTENV"):
    load_dotenv(PROJECT_ROOT / ENVIRONMENT_FILE_NAME)

configured_discord_token = os.getenv("DISCORD_TOKEN")
if not configured_discord_token:
    raise RuntimeError("DISCORD_TOKEN is required")
DISCORD_TOKEN = configured_discord_token

BOT_TIMEZONE = ZoneInfo(os.getenv("BOT_TIMEZONE", "Europe/London"))


def read_clock_setting(setting_name: str, default_clock: str) -> str:
    """Return a validated HH:MM setting, refusing to start on one that cannot be read."""
    clock = parse_clock(os.getenv(setting_name, default_clock))
    if clock is None:
        raise RuntimeError(f"{setting_name} must be a time of day such as {default_clock}")
    return clock


# Fallbacks for servers whose /setup daily chose no time of their own.
DAILY_POST_TIME = read_clock_setting("DAILY_POST_TIME", "17:00")
DAILY_RESET_TIME = read_clock_setting("DAILY_RESET_TIME", "04:00")
DATABASE_PATH = PROJECT_ROOT / os.getenv("DATABASE_PATH", "krillbot.db")
LOG_PATH = PROJECT_ROOT / os.getenv(
    "LOG_PATH", "logs/krillbot-dev.log" if DEVELOPMENT_MODE else "logs/krillbot.log"
)


def parse_guild_ids(raw_guild_ids: str | None) -> tuple[int, ...]:
    """Return numeric Discord server identifiers from a comma-separated setting."""
    if raw_guild_ids is None or not raw_guild_ids.strip():
        return ()

    guild_ids: list[int] = []
    for candidate in raw_guild_ids.replace(" ", "").split(","):
        if not candidate.isdigit():
            raise RuntimeError("GUILD_IDS must contain only comma-separated integers")
        guild_ids.append(int(candidate))
    return tuple(guild_ids)


GUILD_IDS = parse_guild_ids(os.getenv("GUILD_IDS"))
