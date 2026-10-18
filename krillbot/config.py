"""Validated settings loaded from the repository environment file."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

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
