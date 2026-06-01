from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
ENVIRONMENT = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(("html", "xml")),
    trim_blocks=True,
    lstrip_blocks=True,
)

REPORT_TITLE_RE = re.compile(r"^#\s+(?P<title>.+?)\s*$")
REPORT_SECTION_RE = re.compile(r"^(?P<hashes>##)\s+(?P<title>.+?)\s*$")
REPORT_SUBHEADING_RE = re.compile(r"^(?P<hashes>#{3,6})\s+(?P<title>.+?)\s*$")
REPORT_IMAGE_RE = re.compile(r"^!\[(?P<alt>.*?)\]\((?P<src>.*?)\)\s*$")
REPORT_META_RE = re.compile(r"^\*(?P<label>Figure|Limitation):\s*(?P<text>.+?)\*\s*$")


@dataclass(frozen=True)
class ParsedFigure:
    src: str
    alt: str
    caption: str
    limitation: str | None
    html: str


@dataclass(frozen=True)
class ParsedSection:
    title: str
    anchor: str
    summary: str
    body_html: str
    excerpt_html: str
    bullet_items: tuple[str, ...]
    figures: tuple[ParsedFigure, ...]


@dataclass(frozen=True)
class ParsedReport:
    title: str
    sections: tuple[ParsedSection, ...]


def _render(template_name: str, **context: Any) -> str:
    template = ENVIRONMENT.get_template(template_name)
    return template.render(**context)


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    slug = slug.strip("-")
    return slug or "section"


def _strip_inline_markdown(text: str) -> str:
    stripped = re.sub(r"`([^`]+)`", r"\1", text)
    stripped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", stripped)
    stripped = re.sub(r"\*([^*]+)\*", r"\1", stripped)
    return stripped.strip()


def _render_inline(text: str) -> str:
    rendered = escape(text, quote=True)
    rendered = re.sub(r"`([^`]+)`", lambda match: f"<code>{match.group(1)}</code>", rendered)
    rendered = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda match: f'<a href="{_safe_href(match.group(2))}">{match.group(1)}</a>',
        rendered,
    )
    rendered = re.sub(r"\*([^*]+)\*", lambda match: f"<em>{match.group(1)}</em>", rendered)
    return rendered


def _safe_href(raw_href: str) -> str:
    href = raw_href.strip()
    lower_href = href.lower()
    if lower_href.startswith(("javascript:", "data:", "vbscript:")):
        return "#"
    return escape(href, quote=True)


def _render_paragraph(text: str) -> str:
    return f"<p>{_render_inline(text)}</p>"


def _render_list(items: Sequence[str]) -> str:
    return "<ul>" + "".join(f"<li>{_render_inline(item)}</li>" for item in items) + "</ul>"


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_table_separator(line: str) -> bool:
    cells = _split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells)


def _render_table(lines: Sequence[str]) -> str:
    rows = [_split_table_row(line) for line in lines if line.strip().startswith("|")]
    rows = [row for row in rows if row and not _is_table_separator("|" + "|".join(row) + "|")]
    if not rows:
        return ""
    header, *body_rows = rows
    header_html = "<thead><tr>" + "".join(f"<th>{_render_inline(cell)}</th>" for cell in header) + "</tr></thead>"
    body_html = "<tbody>" + "".join(
        "<tr>" + "".join(f"<td>{_render_inline(cell)}</td>" for cell in row) + "</tr>"
        for row in body_rows
    ) + "</tbody>"
    return f"<table>{header_html}{body_html}</table>"


def _render_heading(level: int, text: str) -> str:
    return f"<h{level}>{_render_inline(text)}</h{level}>"


def _render_figure(figure: ParsedFigure) -> str:
    parts = [
        '<figure class="report-figure">',
        f'<img src="{_safe_href(figure.src)}" alt="{escape(figure.alt, quote=True)}" />',
    ]
    if figure.caption:
        parts.append(f"<figcaption>{_render_inline(figure.caption)}</figcaption>")
    if figure.limitation:
        parts.append(
            f'<p class="report-figure__note">{_render_inline(f"Limitation: {figure.limitation}")}</p>'
        )
    parts.append("</figure>")
    return "".join(parts)


def _parse_figure(lines: Sequence[str], index: int) -> tuple[ParsedFigure, int]:
    image_match = REPORT_IMAGE_RE.match(lines[index].strip())
    if image_match is None:
        raise ValueError("Expected image markdown when parsing figure block")

    src = image_match.group("src").strip()
    alt = image_match.group("alt").strip()
    caption = alt
    limitation: str | None = None
    next_index = index + 1

    while next_index < len(lines) and not lines[next_index].strip():
        next_index += 1

    meta_labels: list[str] = []
    while next_index < len(lines):
        meta_match = REPORT_META_RE.match(lines[next_index].strip())
        if meta_match is None:
            break
        label = meta_match.group("label")
        text = meta_match.group("text").strip()
        meta_labels.append(label)
        if label == "Figure":
            caption = text
        elif label == "Limitation":
            limitation = text
        next_index += 1
        while next_index < len(lines) and not lines[next_index].strip():
            next_index += 1
        if len(meta_labels) >= 2:
            break

    figure = ParsedFigure(
        src=src,
        alt=alt,
        caption=caption,
        limitation=limitation,
        html=_render_figure(ParsedFigure(src=src, alt=alt, caption=caption, limitation=limitation, html="")),
    )
    return figure, next_index


def _render_section_fragment(raw_body: str) -> tuple[str, str, tuple[str, ...], tuple[ParsedFigure, ...], str]:
    lines = raw_body.splitlines()
    body_parts: list[str] = []
    excerpt_parts: list[str] = []
    figures: list[ParsedFigure] = []
    bullet_items: list[str] = []
    paragraph_lines: list[str] = []
    list_items: list[str] = []
    summary = ""
    block_count = 0
    index = 0

    def add_block(html_fragment: str) -> None:
        nonlocal block_count
        body_parts.append(html_fragment)
        if block_count < 4:
            excerpt_parts.append(html_fragment)
        block_count += 1

    def flush_paragraph() -> None:
        nonlocal paragraph_lines, summary
        if not paragraph_lines:
            return
        text = " ".join(part.strip() for part in paragraph_lines if part.strip()).strip()
        paragraph_lines = []
        if not text:
            return
        if not summary:
            summary = _strip_inline_markdown(text)
        add_block(_render_paragraph(text))

    def flush_list() -> None:
        nonlocal list_items
        if not list_items:
            return
        bullet_items.extend(_strip_inline_markdown(item) for item in list_items)
        add_block(_render_list(list_items))
        list_items = []

    while index < len(lines):
        line = lines[index].rstrip()
        stripped = line.strip()

        if not stripped or stripped in {"[PAGEBREAK]", "[TOC]"}:
            flush_paragraph()
            flush_list()
            index += 1
            continue

        heading_match = REPORT_SUBHEADING_RE.match(stripped)
        if heading_match is not None:
            flush_paragraph()
            flush_list()
            level = len(heading_match.group("hashes"))
            add_block(_render_heading(level, heading_match.group("title").strip()))
            index += 1
            continue

        image_match = REPORT_IMAGE_RE.match(stripped)
        if image_match is not None:
            flush_paragraph()
            flush_list()
            figure, index = _parse_figure(lines, index)
            figures.append(figure)
            add_block(figure.html)
            continue

        if stripped.startswith("|"):
            flush_paragraph()
            flush_list()
            table_lines: list[str] = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                table_lines.append(lines[index].strip())
                index += 1
            add_block(_render_table(table_lines))
            continue

        if stripped.startswith("- "):
            flush_paragraph()
            list_items.append(stripped[2:].strip())
            index += 1
            while index < len(lines):
                next_stripped = lines[index].strip()
                if next_stripped.startswith("- "):
                    list_items.append(next_stripped[2:].strip())
                    index += 1
                    continue
                break
            flush_list()
            continue

        paragraph_lines.append(stripped)
        index += 1

    flush_paragraph()
    flush_list()

    body_html = "\n".join(body_parts)
    excerpt_html = "\n".join(excerpt_parts if excerpt_parts else body_parts[:1])
    return body_html, excerpt_html, tuple(bullet_items), tuple(figures), summary


def _parse_report_markdown(report_markdown: str) -> ParsedReport:
    title = "Thesis Microsite"
    sections: list[ParsedSection] = []
    current_title: str | None = None
    current_lines: list[str] = []

    def flush_section() -> None:
        nonlocal current_title, current_lines
        if current_title is None:
            return
        body_html, excerpt_html, bullet_items, figures, summary = _render_section_fragment(
            "\n".join(current_lines).strip()
        )
        sections.append(
            ParsedSection(
                title=current_title,
                anchor=_slugify(current_title),
                summary=summary,
                body_html=body_html,
                excerpt_html=excerpt_html,
                bullet_items=bullet_items,
                figures=figures,
            )
        )
        current_title = None
        current_lines = []

    for line in report_markdown.splitlines():
        title_match = REPORT_TITLE_RE.match(line)
        if title_match is not None and not sections and current_title is None:
            title = title_match.group("title").strip()
            continue

        section_match = REPORT_SECTION_RE.match(line)
        if section_match is not None:
            flush_section()
            current_title = section_match.group("title").strip()
            current_lines = []
            continue

        if current_title is not None:
            current_lines.append(line)

    flush_section()
    return ParsedReport(title=title, sections=tuple(sections))


def build_thesis_microsite_sections(report_markdown: str) -> list[dict[str, Any]]:
    report = _parse_report_markdown(report_markdown)
    total_sections = len(report.sections)
    return [
        {
            "title": section.title,
            "anchor": section.anchor,
            "summary": section.summary,
            "body_html": section.body_html,
            "excerpt_html": section.excerpt_html,
            "bullet_items": list(section.bullet_items),
            "figure_count": len(section.figures),
            "position": index,
            "total": total_sections,
        }
        for index, section in enumerate(report.sections, start=1)
    ]


def build_defense_presentation_slides(report_markdown: str) -> list[dict[str, Any]]:
    report = _parse_report_markdown(report_markdown)
    total_sections = len(report.sections)
    return [
        {
            "title": section.title,
            "anchor": section.anchor,
            "takeaway": section.summary or section.title,
            "body_html": section.excerpt_html or section.body_html,
            "bullets": list(section.bullet_items[:4]),
            "image_path": section.figures[0].src if section.figures else None,
            "image_alt": section.figures[0].alt if section.figures else section.title,
            "image_caption": section.figures[0].caption if section.figures else None,
            "citation": section.figures[0].limitation if section.figures else None,
            "note": f"Derived from the long-form report section {index} of {total_sections}.",
            "position": index,
            "total": total_sections,
        }
        for index, section in enumerate(report.sections, start=1)
    ]


def render_thesis_microsite(title: str, sections: Sequence[Mapping[str, Any]]) -> str:
    return _render("thesis_microsite.html", title=title, sections=list(sections))


def render_defense_presentation(title: str, slides: Sequence[Mapping[str, Any]]) -> str:
    return _render("defense_presentation.html", title=title, slides=list(slides))
