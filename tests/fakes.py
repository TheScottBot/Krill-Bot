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
    view: discord.ui.View | None = None


@dataclass(frozen=True)
class EditedMessage:
    """One edit a button press made to the message holding it."""

    content: str | None
    view: discord.ui.View | None
    allowed_mentions: discord.AllowedMentions | None


class FakeInteractionResponse:
    """Capture the first response sent for an interaction."""

    def __init__(self) -> None:
        self.sent_responses: list[SentResponse] = []
        self.edited_messages: list[EditedMessage] = []

    def is_done(self) -> bool:
        """Return whether an initial response has been sent."""
        return bool(self.sent_responses or self.edited_messages)

    async def send_message(
        self,
        content: str | None = None,
        *,
        embed: discord.Embed | None = None,
        ephemeral: bool = False,
        allowed_mentions: discord.AllowedMentions | None = None,
        view: discord.ui.View | None = None,
    ) -> None:
        self.sent_responses.append(SentResponse(content, embed, ephemeral, allowed_mentions, view))

    async def edit_message(
        self,
        *,
        content: str | None = None,
        view: discord.ui.View | None = None,
        allowed_mentions: discord.AllowedMentions | None = None,
    ) -> None:
        self.edited_messages.append(EditedMessage(content, view, allowed_mentions))


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
        permissions: discord.Permissions | None = None,
        channel_id: int | None = None,
    ) -> None:
        self.channel_id = channel_id
        self.response = FakeInteractionResponse()
        self.followup = FakeInteractionFollowup()
        self.guild_id = guild_id
        self.user = type("FakeUser", (), {"id": user_id})()
        self.client = client
        # discord.py's permission checks read the invoking member's resolved permissions.
        self.permissions = discord.Permissions.none() if permissions is None else permissions

    @property
    def last_response(self) -> SentResponse:
        """Return the most recently captured response."""
        return self.response.sent_responses[-1]


class FakeMessage:
    """The selected-message surface needed by the context menu."""

    def __init__(self, *, author_id: int, content: str) -> None:
        self.author = type("FakeAuthor", (), {"id": author_id})()
        self.content = content


@dataclass(frozen=True)
class SentChannelMessage:
    """One message captured from a fake channel."""

    embed: discord.Embed | None
    allowed_mentions: discord.AllowedMentions | None


class FakeChannel:
    """A channel or thread the daily post can be sent to, optionally failing."""

    def __init__(self, *, channel_id: int, send_error: Exception | None = None) -> None:
        self.id = channel_id
        self.send_error = send_error
        self.sent_messages: list[SentChannelMessage] = []

    async def send(
        self,
        *,
        embed: discord.Embed | None = None,
        allowed_mentions: discord.AllowedMentions | None = None,
    ) -> None:
        if self.send_error is not None:
            raise self.send_error
        self.sent_messages.append(SentChannelMessage(embed, allowed_mentions))


class FakeClient:
    """The client surface the daily post needs: finding a channel by its ID."""

    def __init__(self, *channels: FakeChannel) -> None:
        self.channels_by_id = {channel.id: channel for channel in channels}

    def get_channel(self, channel_id: int, /) -> FakeChannel | None:
        return self.channels_by_id.get(channel_id)
