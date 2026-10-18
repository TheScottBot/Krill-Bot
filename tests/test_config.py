"""Configuration contract tests."""

from __future__ import annotations

import os
import subprocess
import sys


def test_import_refuses_a_missing_discord_token() -> None:
    environment = os.environ.copy()
    environment.pop("DISCORD_TOKEN", None)
    environment["KRILLBOT_NO_DOTENV"] = "1"

    completed = subprocess.run(
        [sys.executable, "-c", "import krillbot.config"],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )

    assert completed.returncode != 0
    assert "DISCORD_TOKEN is required" in completed.stderr


def import_config_with(**settings: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["KRILLBOT_NO_DOTENV"] = "1"
    environment["DISCORD_TOKEN"] = "test-token"
    for setting_name in ("DAILY_POST_TIME", "DAILY_RESET_TIME"):
        environment.pop(setting_name, None)
    environment.update(settings)
    return subprocess.run(
        [
            sys.executable,
            "-c",
            "from krillbot import config; print(config.DAILY_POST_TIME, config.DAILY_RESET_TIME)",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )


def test_daily_times_default_to_five_pm_posts_and_four_am_resets() -> None:
    completed = import_config_with()

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.split() == ["17:00", "04:00"]


def test_daily_times_are_read_from_the_environment() -> None:
    completed = import_config_with(DAILY_POST_TIME="6pm", DAILY_RESET_TIME="05:30")

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.split() == ["18:00", "05:30"]


def test_import_refuses_an_unreadable_daily_time() -> None:
    completed = import_config_with(DAILY_RESET_TIME="soon")

    assert completed.returncode != 0
    assert "DAILY_RESET_TIME must be a time of day" in completed.stderr
