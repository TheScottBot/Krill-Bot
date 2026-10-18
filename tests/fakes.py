"""Small Discord interaction doubles shared by command tests."""

from __future__ import annotations

from collections.abc import Coroutine
from dataclasses import dataclass
from typing import Any

import discord


def complete_immediate_coroutine(coroutine: Coroutine[Any, Any, Any]) -> None:
    """Complete a fake-only coroutine whose awaited methods never suspend."""
    try:
        coroutine.send(None)
    except StopIteration:
        return
    finally:
        coroutine.close()
    raise AssertionError("Fake command coroutine unexpectedly suspended")


@dataclass(frozen=True)
class SentResponse:
    """One response captured from a fake interaction."""

    content: str | None
    embed: discord.Embed | None
    ephemeral: bool
    allowed_mentions: discord.AllowedMentions | None


class FakeInteractionResponse:
    """Capture the first response sent for an interaction."""

    def __init__(self) -> None:
        self.sent_responses: list[SentResponse] = []

    def is_done(self) -> bool:
        """Return whether an initial response has been sent."""
        return bool(self.sent_responses)

    async def send_message(
        self,
        content: str | None = None,
        *,
        embed: discord.Embed | None = None,
        ephemeral: bool = False,
        allowed_mentions: discord.AllowedMentions | None = None,
    ) -> None:
        self.sent_responses.append(SentResponse(content, embed, ephemeral, allowed_mentions))


class FakeInteractionFollowup:
    """Capture additional private pages sent after the initial response."""

    def __init__(self) -> None:
        self.sent_responses: list[SentResponse] = []

    async def send(
        self,
        content: str | None = None,
        *,
        embed: discord.Embed | None = None,
        ephemeral: bool = False,
        allowed_mentions: discord.AllowedMentions | None = None,
    ) -> None:
        self.sent_responses.append(SentResponse(content, embed, ephemeral, allowed_mentions))


class FakeInteraction:
    """The interaction surface needed by KE1 command tests."""

    def __init__(
        self,
        *,
        guild_id: int | None = None,
        user_id: int = 100,
        client: Any = None,
    ) -> None:
        self.response = FakeInteractionResponse()
        self.followup = FakeInteractionFollowup()
        self.guild_id = guild_id
        self.user = type("FakeUser", (), {"id": user_id})()
        self.client = client

    @property
    def last_response(self) -> SentResponse:
        """Return the most recently captured response."""
        return self.response.sent_responses[-1]


class FakeMessage:
    """The selected-message surface needed by the context menu."""

    def __init__(self, *, author_id: int, content: str) -> None:
        self.author = type("FakeAuthor", (), {"id": author_id})()
        self.content = content
