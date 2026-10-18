"""Application-command tests for the KE1 surface."""

from __future__ import annotations

import discord

from krillbot import commands
from tests.fakes import FakeInteraction, complete_immediate_coroutine


def test_help_identifies_the_bot_as_unofficial_and_disables_mentions() -> None:
    interaction = FakeInteraction()

    complete_immediate_coroutine(commands.help_command.callback(interaction))

    response = interaction.last_response
    assert response.embed is not None
    assert response.embed.title == "Krill Bot"
    assert "unofficial" in response.embed.description.lower()
    assert response.allowed_mentions is not None
    assert response.allowed_mentions.to_dict() == discord.AllowedMentions.none().to_dict()
