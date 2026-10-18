"""Generate the GitHub Pages privacy and terms pages from their Markdown records.

`PRIVACY.md` and `TERMS.md` are the only copies of their text. The pages under
`docs/` are derived from them, and `--check` fails when a page and its source
differ, so the site cannot drift from the records (datum 0.7).

The converter understands only the Markdown those records use: two heading
levels, paragraphs, bulleted lists, tables, inline code and bare web
addresses. Anything else is refused rather than rendered wrongly.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

GENERATED_PAGES = (
    ("PRIVACY.md", "privacy.html"),
    ("TERMS.md", "terms.html"),
)
SITE_DIRECTORY_NAME = "docs"
_UNSUPPORTED_BLOCK = re.compile(r"(?:#|```|>|\d+\.\s)")
_WEB_ADDRESS = re.compile(r"https://[^\s<>()]*[^\s<>().,;:]")
_PAGE_TEMPLATE = """<!doctype html>
<html lang="en-GB">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="generator" content="site_builder.py from {source_name}">
  <title>{title} · Krill Bot</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
<main>
<p><a href="./">Krill Bot</a></p>
{body}
</main>
<footer>
  <a href="./">Home</a>
  <a href="privacy.html">Privacy</a>
  <a href="terms.html">Terms</a>
</footer>
</body>
</html>
"""


class UnsupportedMarkdownError(ValueError):
    """The source uses Markdown the builder would render wrongly."""


def _inline_html(text: str) -> str:
    segments = text.split("`")
    if len(segments) % 2 == 0:
        raise UnsupportedMarkdownError(f"unbalanced inline code in: {text}")
    rendered_segments: list[str] = []
    for segment_index, segment in enumerate(segments):
        escaped_segment = html.escape(segment, quote=False)
        if segment_index % 2 == 1:
            rendered_segments.append(f"<code>{escaped_segment}</code>")
            continue
        rendered_segments.append(
            _WEB_ADDRESS.sub(
                lambda address_match: (
                    f'<a href="{address_match.group(0)}">{address_match.group(0)}</a>'
                ),
                escaped_segment,
            )
        )
    return "".join(rendered_segments)


def _starts_block(line_text: str) -> bool:
    return line_text.startswith(("#", "- ", "|", "```", ">")) or bool(
        re.match(r"\d+\.\s", line_text)
    )


def _table_cells(line_text: str) -> list[str]:
    return [cell.strip() for cell in line_text.strip().strip("|").split("|")]


def markdown_to_html(markdown_text: str) -> str:
    """Convert the supported Markdown subset to HTML blocks joined by newlines."""
    lines = markdown_text.splitlines()
    blocks: list[str] = []
    line_index = 0
    while line_index < len(lines):
        line_text = lines[line_index]
        if not line_text.strip():
            line_index += 1
        elif line_text.startswith("## "):
            blocks.append(f"<h2>{_inline_html(line_text[3:].strip())}</h2>")
            line_index += 1
        elif line_text.startswith("# "):
            blocks.append(f"<h1>{_inline_html(line_text[2:].strip())}</h1>")
            line_index += 1
        elif _UNSUPPORTED_BLOCK.match(line_text):
            raise UnsupportedMarkdownError(f"unsupported block: {line_text}")
        elif line_text.startswith("- "):
            items: list[list[str]] = []
            while line_index < len(lines) and (
                lines[line_index].startswith("- ") or lines[line_index].startswith("  ")
            ):
                if lines[line_index].startswith("- "):
                    items.append([lines[line_index][2:].strip()])
                else:
                    items[-1].append(lines[line_index].strip())
                line_index += 1
            list_items = "\n".join(f"<li>{_inline_html(' '.join(item))}</li>" for item in items)
            blocks.append(f"<ul>\n{list_items}\n</ul>")
        elif line_text.startswith("|"):
            table_lines: list[str] = []
            while line_index < len(lines) and lines[line_index].startswith("|"):
                table_lines.append(lines[line_index])
                line_index += 1
            if len(table_lines) < 2 or set(table_lines[1].replace("|", "").strip()) != {"-"}:
                raise UnsupportedMarkdownError(f"table without a separator row: {table_lines[0]}")
            header_cells = "".join(
                f"<th>{_inline_html(cell)}</th>" for cell in _table_cells(table_lines[0])
            )
            body_rows = "\n".join(
                "<tr>"
                + "".join(f"<td>{_inline_html(cell)}</td>" for cell in _table_cells(row_line))
                + "</tr>"
                for row_line in table_lines[2:]
            )
            blocks.append(
                f"<table>\n<thead>\n<tr>{header_cells}</tr>\n</thead>\n"
                f"<tbody>\n{body_rows}\n</tbody>\n</table>"
            )
        else:
            paragraph_lines: list[str] = []
            while (
                line_index < len(lines)
                and lines[line_index].strip()
                and not _starts_block(lines[line_index])
            ):
                paragraph_lines.append(lines[line_index].strip())
                line_index += 1
            blocks.append(f"<p>{_inline_html(' '.join(paragraph_lines))}</p>")
    return "\n".join(blocks)


def _page_title(markdown_text: str) -> str:
    for line_text in markdown_text.splitlines():
        if line_text.startswith("# "):
            return html.escape(line_text[2:].strip(), quote=False)
    raise UnsupportedMarkdownError("a page source needs a level one heading")


def build_pages(project_root: Path) -> dict[Path, str]:
    """Return every generated page's path and its expected content."""
    built_pages: dict[Path, str] = {}
    for source_name, page_name in GENERATED_PAGES:
        markdown_text = (project_root / source_name).read_text(encoding="utf-8")
        built_pages[project_root / SITE_DIRECTORY_NAME / page_name] = _PAGE_TEMPLATE.format(
            source_name=source_name,
            title=_page_title(markdown_text),
            body=markdown_to_html(markdown_text),
        )
    return built_pages


def stale_pages(project_root: Path) -> list[str]:
    """Return the generated pages that are missing or differ from their sources."""
    return [
        page_path.name
        for page_path, page_content in build_pages(project_root).items()
        if not page_path.is_file() or page_path.read_text(encoding="utf-8") != page_content
    ]


def write_pages(project_root: Path) -> None:
    """Write every generated page from its source."""
    for page_path, page_content in build_pages(project_root).items():
        page_path.write_text(page_content, encoding="utf-8", newline="\n")


def main(arguments: list[str]) -> int:
    """Build the pages, or with --check report those that need rebuilding."""
    project_root = Path(__file__).resolve().parent
    if arguments == ["--check"]:
        outdated_pages = stale_pages(project_root)
        for page_name in outdated_pages:
            print(f"{SITE_DIRECTORY_NAME}/{page_name} differs from its source; run site_builder.py")
        return 1 if outdated_pages else 0
    if arguments:
        print("usage: site_builder.py [--check]")
        return 2
    write_pages(project_root)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
