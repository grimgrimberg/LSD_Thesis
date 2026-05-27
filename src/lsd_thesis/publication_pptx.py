from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from lsd_thesis.publication_html import build_defense_presentation_slides


def _find_slide(
    slides: list[dict[str, Any]],
    prefix: str,
) -> dict[str, Any]:
    for slide in slides:
        title = str(slide.get("title", ""))
        if title.startswith(prefix):
            return slide
    raise KeyError(f"Report slide starting with {prefix!r} not found")


def _compact_text(text: str | None) -> str:
    return " ".join((text or "").split()).strip()


def _merge_bullets(
    source_slides: list[dict[str, Any]],
    *,
    max_items: int = 5,
) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()

    for slide in source_slides:
        takeaway = _compact_text(str(slide.get("takeaway", "")))
        if takeaway and takeaway not in seen:
            merged.append(takeaway)
            seen.add(takeaway)

        for bullet in slide.get("bullets", []):
            clean_bullet = _compact_text(str(bullet))
            if clean_bullet and clean_bullet not in seen:
                merged.append(clean_bullet)
                seen.add(clean_bullet)
            if len(merged) >= max_items:
                return merged[:max_items]

    return merged[:max_items]


def _make_slide(
    title: str,
    source_slides: list[dict[str, Any]],
    *,
    image_from: dict[str, Any] | None = None,
) -> dict[str, Any]:
    anchor = "-".join(title.lower().replace(":", "").split())
    image_slide = image_from or next(
        (slide for slide in source_slides if slide.get("image_path")),
        None,
    )
    return {
        "title": title,
        "anchor": anchor,
        "takeaway": _compact_text(str(source_slides[0].get("takeaway", ""))) if source_slides else "",
        "bullets": _merge_bullets(source_slides),
        "image_path": image_slide.get("image_path") if image_slide else None,
        "image_alt": image_slide.get("image_alt") if image_slide else title,
        "image_caption": image_slide.get("image_caption") if image_slide else None,
        "citation": image_slide.get("citation") if image_slide else None,
        "note": "Derived from the long-form thesis report.",
    }


def build_defense_pptx_slides(report_markdown: str) -> list[dict[str, Any]]:
    source_slides = build_defense_presentation_slides(report_markdown)

    executive = _find_slide(source_slides, "Executive Summary")
    abstract = _find_slide(source_slides, "Abstract")
    intro = _find_slide(source_slides, "1. Introduction")
    objectives = _find_slide(source_slides, "2. Research Objectives")
    scope = _find_slide(source_slides, "3. Scientific Scope")
    architecture = _find_slide(source_slides, "4. Repository Architecture")
    model = _find_slide(source_slides, "5. Mathematical Model")
    data = _find_slide(source_slides, "6. Empirical Data Source")
    extraction = _find_slide(source_slides, "7. Macro-Module Extraction")
    observables = _find_slide(source_slides, "8. Shared Observable Space")
    stage1 = _find_slide(source_slides, "9. Stage 1")
    stage2 = _find_slide(source_slides, "10. Stage 2")
    stage3 = _find_slide(source_slides, "11. Stage 3")
    stage4 = _find_slide(source_slides, "12. Stage 4")
    dashboard = _find_slide(source_slides, "13. Dashboard")
    training = _find_slide(source_slides, "14. Training")
    worked = _find_slide(source_slides, "15. What Worked")
    weak = _find_slide(source_slides, "16. What Did Not Work")
    threats = _find_slide(source_slides, "17. Threats to Validity")
    claims = _find_slide(source_slides, "18. Defendable Thesis Claims")
    reproducibility = _find_slide(source_slides, "19. Reproducibility")
    conclusion = _find_slide(source_slides, "20. Conclusion")

    title_slide = {
        "title": "Transparent Surrogate Modeling of Altered-State-Inspired Macro-Dynamics",
        "anchor": "title-slide",
        "takeaway": _compact_text(str(executive.get("takeaway", ""))),
        "bullets": _merge_bullets([abstract, intro], max_items=4),
        "image_path": None,
        "image_alt": "Title slide",
        "image_caption": None,
        "citation": None,
        "note": "Defense opening framing slide.",
    }

    cv5_slide = {
        "title": "CV5 Internal Validation",
        "anchor": "cv5-internal-validation",
        "takeaway": (
            "Approved preliminary five-fold subject-disjoint internal validation is complete; "
            "this is not external or clinical validation."
        ),
        "bullets": [
            "Five folds cover the 15 complete paired subjects, with 3 held out per fold.",
            "Fold metrics are descriptive internal-validation summaries, not confidence intervals.",
            "No subject-level motion, FD/DVARS, confound, or censoring stratification was available.",
            "The selected perturbation family is a proxy-objective result, not proof of a biological mechanism.",
        ],
        "image_path": None,
        "image_alt": "CV5 internal validation summary",
        "image_caption": None,
        "citation": "Internal validation only; not external or clinical validation, and not subjective-state evidence.",
        "note": "Defense scope slide derived from the CV5 validation section.",
    }

    deck = [
        title_slide,
        _make_slide("Scope and Claim Boundaries", [executive, abstract, objectives, scope]),
        _make_slide("Repository Workflow", [architecture]),
        _make_slide("Model Assumptions", [model]),
        _make_slide("Dataset and Macro-Module Extraction", [data, extraction]),
        _make_slide("Shared Observable Space", [observables]),
        _make_slide("Stage 1 Synthetic Shift", [stage1], image_from=stage1),
        _make_slide("Stage 2 Empirical Bridge and Fit", [stage2], image_from=stage2),
        cv5_slide,
        _make_slide("Stage 3 Perturbation-Family Ranking", [stage3]),
        _make_slide("Stage 4 Ablation and Pairwise Tests", [stage4]),
        _make_slide("Dashboard and Artifact Layer", [dashboard]),
        _make_slide("Training Benchmarks", [training]),
        _make_slide("What Worked, What Failed, and Validity Risks", [worked, weak, threats]),
        _make_slide("Defendable Conclusion", [claims, reproducibility, conclusion]),
    ]

    for index, slide in enumerate(deck, start=1):
        slide["position"] = index
        slide["total"] = len(deck)
    return deck


def write_defense_pptx_spec(slides: list[dict[str, Any]], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(slides, indent=2), encoding="utf-8")
    return output_path


def build_defense_presentation_pptx(
    repo_root: Path,
    slides: list[dict[str, Any]],
    output_path: Path,
) -> Path:
    tool_dir = repo_root / "tools" / "pptx"
    node_package = tool_dir / "node_modules" / "pptxgenjs"
    script_path = tool_dir / "build_defense_deck.mjs"
    spec_path = output_path.with_suffix(".json")

    if not script_path.exists():
        raise FileNotFoundError(f"PPTX generator script not found: {script_path}")
    if not node_package.exists():
        raise FileNotFoundError(
            f"PptxGenJS dependency not found: {node_package}. Run `npm ci --prefix tools/pptx`."
        )

    write_defense_pptx_spec(slides, spec_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["node", str(script_path), str(spec_path), str(output_path)],
        check=True,
        cwd=repo_root,
    )
    if not output_path.exists():
        raise FileNotFoundError(f"PPTX build completed without output file: {output_path}")
    return output_path
