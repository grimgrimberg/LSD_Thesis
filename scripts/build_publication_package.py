from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

# ruff: noqa: E402
from lsd_thesis.docx_export import markdown_to_docx
from lsd_thesis.publication import build_publication_evidence
from lsd_thesis.publication_content import (
    build_defense_outline_markdown,
    build_thesis_report_markdown,
)
from lsd_thesis.publication_figures import generate_publication_figures
from lsd_thesis.publication_html import (
    build_defense_presentation_slides,
    build_thesis_microsite_sections,
    render_defense_presentation,
    render_thesis_microsite,
)
from lsd_thesis.publication_pptx import (
    build_defense_pptx_slides,
    build_defense_presentation_pptx,
)

OUTPUT_DIR = REPO_ROOT / "output" / "doc"
FIGURES_DIR = OUTPUT_DIR / "figures"


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def build_publication_package(repo_root: Path = REPO_ROOT) -> dict[str, Path]:
    output_dir = repo_root / "output" / "doc"
    figures_dir = output_dir / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    evidence = build_publication_evidence(repo_root)
    figure_bundle = generate_publication_figures(evidence, figures_dir)

    thesis_markdown = build_thesis_report_markdown(evidence, figure_bundle)
    defense_markdown = build_defense_outline_markdown(evidence)
    thesis_sections = build_thesis_microsite_sections(thesis_markdown)
    defense_slides = build_defense_presentation_slides(thesis_markdown)
    defense_pptx_slides = build_defense_pptx_slides(thesis_markdown)

    thesis_markdown_path = _write_text(output_dir / "thesis_report_revised.md", thesis_markdown)
    defense_markdown_path = _write_text(output_dir / "defense_outline.md", defense_markdown)

    thesis_docx_path = output_dir / "thesis_report_revised.docx"
    defense_docx_path = output_dir / "defense_outline.docx"
    markdown_to_docx(thesis_markdown_path, thesis_docx_path)
    markdown_to_docx(defense_markdown_path, defense_docx_path)

    thesis_microsite_path = _write_text(
        output_dir / "thesis_microsite.html",
        render_thesis_microsite(title="Thesis Microsite", sections=thesis_sections),
    )
    defense_presentation_path = _write_text(
        output_dir / "defense_presentation.html",
        render_defense_presentation(title="Defense Presentation", slides=defense_slides),
    )
    defense_presentation_pptx_path = build_defense_presentation_pptx(
        repo_root,
        defense_pptx_slides,
        output_dir / "defense_presentation.pptx",
    )

    outputs = {
        "thesis_report_markdown": thesis_markdown_path,
        "thesis_report_docx": thesis_docx_path,
        "defense_outline_markdown": defense_markdown_path,
        "defense_outline_docx": defense_docx_path,
        "thesis_microsite_html": thesis_microsite_path,
        "defense_presentation_html": defense_presentation_path,
        "defense_presentation_pptx": defense_presentation_pptx_path,
    }
    outputs.update({figure.figure_id: figure.path for figure in figure_bundle.values()})
    return outputs


def main() -> None:
    outputs = build_publication_package(REPO_ROOT)
    for name, path in outputs.items():
        print(f"{name}: {path}")


if __name__ == "__main__":
    main()
