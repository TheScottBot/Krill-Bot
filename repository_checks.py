"""Executable tree-wide policy checks used by tests and continuous integration."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".md",
    ".py",
    ".service",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}
PROHIBITED_DASH_CHARACTERS = {"\u2013", "\u2014"}
MANGLED_HYPHEN_RUN = re.compile(r"(?<!-)" + "-" * 2 + r"(?:-)?(?!-)")
COMMAND_FLAG = re.compile(r"(?<![A-Za-z0-9-])" + "-" * 2 + r"[a-z0-9][a-z0-9-]*\b")
MARKDOWN_SEPARATOR = re.compile(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$")
RESPONSE_METHOD_NAMES = {"send", "send_message"}


def owned_text_files(root_path: Path) -> list[Path]:
    """Return owned text files while excluding generated and tool-state directories."""
    return sorted(
        candidate_path
        for candidate_path in root_path.rglob("*")
        if candidate_path.is_file()
        and candidate_path.suffix.lower() in TEXT_SUFFIXES
        and not EXCLUDED_DIRECTORY_NAMES.intersection(candidate_path.relative_to(root_path).parts)
    )


def find_prohibited_typography(root_path: Path) -> list[str]:
    """Report prohibited dash characters and converter-mangled hyphen runs."""
    findings: list[str] = []
    for text_file_path in owned_text_files(root_path):
        for line_number, line_text in enumerate(
            text_file_path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if PROHIBITED_DASH_CHARACTERS.intersection(line_text):
                findings.append(f"{text_file_path}:{line_number}: prohibited dash character")
            if MARKDOWN_SEPARATOR.fullmatch(line_text):
                continue
            without_flags = COMMAND_FLAG.sub("", line_text)
            if MANGLED_HYPHEN_RUN.search(without_flags):
                findings.append(f"{text_file_path}:{line_number}: prohibited hyphen run")
    return findings


def find_user_facing_literals(package_path: Path) -> list[str]:
    """Report literal response text outside the module that owns displayed copy."""
    findings: list[str] = []
    for source_file_path in sorted(package_path.rglob("*.py")):
        if source_file_path.name == "embeds.py":
            continue
        parsed = ast.parse(
            source_file_path.read_text(encoding="utf-8"),
            filename=str(source_file_path),
        )
        for syntax_node in ast.walk(parsed):
            if not isinstance(syntax_node, ast.Call):
                continue
            if not isinstance(syntax_node.func, ast.Attribute):
                continue
            if syntax_node.func.attr not in RESPONSE_METHOD_NAMES:
                continue
            supplied_values = list(syntax_node.args) + [
                keyword.value for keyword in syntax_node.keywords
            ]
            if any(
                isinstance(supplied_value, ast.Constant) and isinstance(supplied_value.value, str)
                for supplied_value in supplied_values
            ):
                findings.append(
                    f"{source_file_path}:{syntax_node.lineno}: "
                    "user-facing string must be owned by embeds.py"
                )
    return findings


def main() -> int:
    """Print every repository policy finding and return a process status."""
    project_root = Path(__file__).resolve().parent
    findings = find_prohibited_typography(project_root)
    findings.extend(find_user_facing_literals(project_root / "krillbot"))
    for finding in findings:
        print(finding)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
