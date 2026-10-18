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
