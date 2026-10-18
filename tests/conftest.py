"""Shared isolation for the Krill Bot test suite."""

from __future__ import annotations

import os

os.environ["KRILLBOT_NO_DOTENV"] = "1"
os.environ["DISCORD_TOKEN"] = "test-token"
