"""Tree-wide architectural checks."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from repository_checks import find_prohibited_typography, find_user_facing_literals

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PURE_MODULE_PATHS = (
    PROJECT_ROOT / "krillbot" / "result_grammar.py",
    PROJECT_ROOT / "krillbot" / "boards.py",
)
FORBIDDEN_PURE_IMPORTS = {"discord", "sqlite3"}


@pytest.mark.parametrize("module_path", PURE_MODULE_PATHS)
def test_portable_logic_has_no_platform_or_storage_imports(module_path: Path) -> None:
    parsed = ast.parse(module_path.read_text(encoding="utf-8"), filename=str(module_path))
    imported_roots = {
        imported.name.split(".", maxsplit=1)[0]
        for statement in ast.walk(parsed)
        if isinstance(statement, ast.Import)
        for imported in statement.names
    }
    imported_roots.update(
        statement.module.split(".", maxsplit=1)[0]
        for statement in ast.walk(parsed)
        if isinstance(statement, ast.ImportFrom) and statement.module is not None
    )

    assert imported_roots.isdisjoint(FORBIDDEN_PURE_IMPORTS)


def test_owned_tree_has_no_prohibited_typography() -> None:
    assert find_prohibited_typography(PROJECT_ROOT) == []


def test_user_facing_strings_are_owned_by_embeds_module() -> None:
    assert find_user_facing_literals(PROJECT_ROOT / "krillbot") == []


def test_package_metadata_declares_the_settled_runtime_and_dependencies() -> None:
    project_configuration = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'requires-python = ">=3.14"' in project_configuration
    assert '"discord.py>=2.7.1"' in project_configuration
    assert '"python-dotenv>=1.2.4"' in project_configuration
    assert '"tzdata>=2026.5"' in project_configuration
    assert '"pytest>=9.1.1"' in project_configuration
    assert '"hypothesis>=6.167.1"' in project_configuration
    assert '"ruff>=0.16.8"' in project_configuration
    assert '"mypy>=2.4.0"' in project_configuration
    assert "strict = true" in project_configuration


def test_dependency_record_covers_every_declared_dependency_and_datum_field() -> None:
    dependency_record = (PROJECT_ROOT / "DEPENDENCIES.md").read_text(encoding="utf-8")

    for dependency_name in (
        "discord.py",
        "python-dotenv",
        "tzdata",
        "pytest",
        "Hypothesis",
        "Ruff",
        "MyPy",
    ):
        assert f"## {dependency_name}" in dependency_record

    for field_name in (
        "Behaviour provided:",
        "Why the standard library or platform is insufficient:",
        "Maintenance status:",
        "Licence:",
        "Size:",
        "Platform support:",
        "Security implications:",
        "Test strategy:",
        "Replacement cost:",
    ):
        assert dependency_record.count(field_name) == 7


def test_mit_licence_records_the_author_selected_holder() -> None:
    licence_text = (PROJECT_ROOT / "LICENCE").read_text(encoding="utf-8")

    assert licence_text.startswith("MIT License\n")
    assert "Copyright (c) 2026 TheScottBot" in licence_text
    assert "Permission is hereby granted, free of charge" in licence_text
    assert 'THE SOFTWARE IS PROVIDED "AS IS"' in licence_text


def test_environment_example_names_every_configured_setting() -> None:
    environment_example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")

    for setting_name in (
        "DISCORD_TOKEN",
        "GUILD_IDS",
        "BOT_TIMEZONE",
        "DATABASE_PATH",
        "LOG_PATH",
    ):
        assert f"{setting_name}=" in environment_example


def test_continuous_integration_runs_every_ke1_gate() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    for command_text in (
        "python repository_checks.py",
        "ruff check .",
        "ruff format --check .",
        "mypy krillbot repository_checks.py",
        "pytest",
        "pytest tests/test_result_grammar.py",
    ):
        assert command_text in workflow


def test_systemd_service_uses_the_stable_launcher_and_hardening() -> None:
    service = (PROJECT_ROOT / "deploy" / "krillbot.service").read_text(encoding="utf-8")

    assert "ExecStart=/opt/krillbot/.venv/bin/python /opt/krillbot/bot.py" in service
    assert "NoNewPrivileges=true" in service
    assert "PrivateTmp=true" in service
    assert "ProtectSystem=strict" in service
    assert "ReadWritePaths=/opt/krillbot" in service


def test_continuous_integration_runs_the_suite_under_python_development_mode() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "python -X dev -m pytest -W error" in workflow


def test_testing_record_states_what_python_offers_for_memory_analysis() -> None:
    testing_record = (PROJECT_ROOT / "TESTING.md").read_text(encoding="utf-8")

    assert "## Memory and undefined behaviour analysis" in testing_record
    assert "python -X dev -m pytest -W error" in testing_record
