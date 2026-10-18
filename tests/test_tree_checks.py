"""Tests for executable repository-wide policy checks."""

from __future__ import annotations

from pathlib import Path

from repository_checks import find_prohibited_typography, find_user_facing_literals


def test_prose_check_reports_prohibited_dash_characters(tmp_path: Path) -> None:
    prose_file = tmp_path / "example.md"
    prose_file.write_text("wrong\u2014dash\n", encoding="utf-8")

    assert find_prohibited_typography(tmp_path) == [f"{prose_file}:1: prohibited dash character"]


def test_prose_check_allows_markdown_table_separators_and_command_flags(
    tmp_path: Path,
) -> None:
    prose_file = tmp_path / "example.md"
    separator = "|" + "-" * 3 + "|" + "-" * 3 + "|"
    development_flag = "-" * 2 + "dev"
    prose_file.write_text(f"{separator}\nUse `{development_flag}`.\n", encoding="utf-8")

    assert find_prohibited_typography(tmp_path) == []


def test_user_facing_string_check_reports_inline_response_text(tmp_path: Path) -> None:
    package_path = tmp_path / "krillbot"
    package_path.mkdir()
    source_file = package_path / "commands.py"
    source_file.write_text(
        "async def reply(interaction):\n"
        '    await interaction.response.send_message("Inline response")\n',
        encoding="utf-8",
    )

    assert find_user_facing_literals(package_path) == [
        f"{source_file}:2: user-facing string must be owned by embeds.py"
    ]
