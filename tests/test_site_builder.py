"""Tests for the generated GitHub Pages documents."""

from __future__ import annotations

from pathlib import Path

import pytest

from krillbot import db
from site_builder import (
    GENERATED_PAGES,
    UnsupportedMarkdownError,
    markdown_to_html,
    stale_pages,
    write_pages,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_headings_and_paragraphs_become_html_with_wrapped_lines_joined() -> None:
    assert markdown_to_html("# Title\n\nFirst line\nsecond line.\n\n## Part\n") == (
        "<h1>Title</h1>\n<p>First line second line.</p>\n<h2>Part</h2>"
    )


def test_lists_keep_their_indented_continuation_lines() -> None:
    assert markdown_to_html("- one item\n  continued\n- two\n") == (
        "<ul>\n<li>one item continued</li>\n<li>two</li>\n</ul>"
    )


def test_tables_become_a_header_and_body() -> None:
    separator_row = "|" + "-" * 3 + "|" + "-" * 3 + "|"
    assert markdown_to_html(f"| Column | Meaning |\n{separator_row}\n| `a` | first |\n") == (
        "<table>\n<thead>\n<tr><th>Column</th><th>Meaning</th></tr>\n</thead>\n"
        "<tbody>\n<tr><td><code>a</code></td><td>first</td></tr>\n</tbody>\n</table>"
    )


def test_text_is_escaped_inside_and_outside_code() -> None:
    assert markdown_to_html("Use `a<b` & <script>.\n") == (
        "<p>Use <code>a&lt;b</code> &amp; &lt;script&gt;.</p>"
    )


def test_bare_web_addresses_become_links() -> None:
    assert markdown_to_html("See https://krillion.io for the game.\n") == (
        '<p>See <a href="https://krillion.io">https://krillion.io</a> for the game.</p>'
    )


@pytest.mark.parametrize("unsupported_text", ["### Deeper\n", "```text\ncode\n```\n", "1. one\n"])
def test_markdown_the_builder_does_not_understand_is_refused(unsupported_text: str) -> None:
    with pytest.raises(UnsupportedMarkdownError):
        markdown_to_html(unsupported_text)


def test_a_page_that_differs_from_its_source_is_reported_until_rebuilt(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    for source_name, _page_name in GENERATED_PAGES:
        (tmp_path / source_name).write_text("# Example\n\nText.\n", encoding="utf-8")

    assert stale_pages(tmp_path) == [page_name for _source_name, page_name in GENERATED_PAGES]

    write_pages(tmp_path)

    assert stale_pages(tmp_path) == []


def test_committed_pages_match_their_sources() -> None:
    assert stale_pages(PROJECT_ROOT) == []


def test_privacy_page_names_every_stored_column() -> None:
    privacy_page = (PROJECT_ROOT / "docs" / "privacy.html").read_text(encoding="utf-8")
    connection = db.initialise(":memory:")
    try:
        table_names = [
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        ]
        stored_names = table_names + [
            column_row[1]
            for table_name in table_names
            for column_row in connection.execute(f"PRAGMA table_info({table_name})")
        ]
    finally:
        connection.close()

    for stored_name in stored_names:
        assert f"<code>{stored_name}</code>" in privacy_page, stored_name


def test_continuous_integration_checks_the_generated_pages() -> None:
    workflow = (PROJECT_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    assert "python site_builder.py --check" in workflow


def test_site_disables_jekyll_so_pages_are_served_as_written() -> None:
    assert (PROJECT_ROOT / "docs" / ".nojekyll").is_file()
