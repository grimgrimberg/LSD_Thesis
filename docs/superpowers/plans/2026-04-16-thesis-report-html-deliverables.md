# Thesis Report And HTML Deliverables Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-source publication package that generates a revised thesis-style report, a DOCX/PDF export, a thesis microsite HTML report, a defense-presentation HTML artifact, a defense outline document, and a static figure pack grounded in the repository's saved results.

**Architecture:** Add a publication pipeline that loads saved Stage 1 to Stage 4 artifacts into a normalized evidence model, renders a reproducible static figure pack from that evidence, and then reuses the same figure narratives to build Markdown, DOCX, and HTML deliverables. Keep the dashboard additive by exposing links to the new outputs instead of rewriting the app.

**Tech Stack:** Python 3.13, `pyyaml`, `matplotlib`, `python-docx`, `jinja2`, FastAPI artifact routing, pytest, ruff

---

## File Structure Map

### New files

- `src/lsd_thesis/publication.py`
  - Load saved JSON and YAML result artifacts into a typed evidence model.
- `src/lsd_thesis/publication_figures.py`
  - Generate static PNG figures plus a figure manifest with caption, observation, interpretation, and limitation text.
- `src/lsd_thesis/publication_content.py`
  - Build the revised thesis report Markdown and the defense outline Markdown from the shared evidence and figure narratives.
- `src/lsd_thesis/publication_html.py`
  - Render the thesis microsite HTML and defense presentation HTML from the same evidence blocks.
- `src/lsd_thesis/docx_export.py`
  - Convert Markdown with image directives into a figure-rich DOCX.
- `src/lsd_thesis/templates/thesis_microsite.html`
- `src/lsd_thesis/templates/defense_presentation.html`
- `tests/test_publication.py`
- `tests/test_publication_figures.py`
- `tests/test_publication_content.py`
- `tests/test_docx_export.py`
- `tests/test_publication_html.py`
- `scripts/build_publication_package.py`

### Modified files

- `pyproject.toml`
- `scripts/generate_report_docx.py`
- `src/lsd_thesis/web/app.py`
- `tests/test_web.py`
- `README.md`

## Task 1: Add Publication Evidence Loader

**Files:**
- Modify: `pyproject.toml`
- Create: `src/lsd_thesis/publication.py`
- Test: `tests/test_publication.py`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
import json
import yaml

from lsd_thesis.publication import build_publication_evidence


def test_build_publication_evidence_collects_stage_metrics(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "results" / "stage_1").mkdir(parents=True)
    (repo_root / "results" / "stage_2").mkdir(parents=True)
    (repo_root / "results" / "stage_3").mkdir(parents=True)
    (repo_root / "results" / "stage_4").mkdir(parents=True)
    (repo_root / "results" / "training" / "condition_benchmark").mkdir(parents=True)
    (repo_root / "results" / "training" / "multitask_benchmark").mkdir(parents=True)
    (repo_root / "configs" / "targets").mkdir(parents=True)

    (repo_root / "results" / "stage_1" / "stage_1_summary.json").write_text(json.dumps({"baseline": {"state_entropy": 0.9890}, "perturbed": {"state_entropy": 0.9976}}), encoding="utf-8")
    (repo_root / "results" / "stage_2" / "stage_2_summary.json").write_text(json.dumps({"initial_score": 5.2439, "best_score": 0.9774, "best_metrics": {"within_network_stability": 0.2913}, "multi_seed_summary": {"mean_metrics": {"within_network_stability": 0.0962}, "std_metrics": {"within_network_stability": 0.0239}}, "empirical_provenance": {"subject_count": 15, "run_count": 60, "dataset_anchor": "OpenNeuro ds003059"}}), encoding="utf-8")
    (repo_root / "results" / "stage_3" / "stage_3_summary.json").write_text(json.dumps({"best_mechanism": "less_hierarchical_constraint", "best_strength": 0.25, "best_score": 3481.53}), encoding="utf-8")
    (repo_root / "results" / "stage_4" / "stage_4_summary.json").write_text(json.dumps({"best_single": {"mechanism": "less_hierarchical_constraint", "score": 3481.53}, "best_pair": {"mechanism_pair": "less_hierarchical_constraint+more_stochasticity", "score": 3498.33}}), encoding="utf-8")
    (repo_root / "results" / "training" / "condition_benchmark" / "comparison_summary.json").write_text(json.dumps({"models": [{"name": "temporal_cnn", "balanced_accuracy": 0.595}]}), encoding="utf-8")
    (repo_root / "results" / "training" / "multitask_benchmark" / "comparison_summary.json").write_text(json.dumps({"models": [{"name": "hist_gradient_boosting_multitask", "eigen_r2": 0.2616}]}), encoding="utf-8")
    (repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml").write_text(yaml.safe_dump({"target_deltas": {"within_network_stability": 0.0661}}), encoding="utf-8")
    (repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml").write_text(yaml.safe_dump({"target_deltas": {"within_network_stability": -0.1}}), encoding="utf-8")

    evidence = build_publication_evidence(repo_root)

    assert evidence.stage2.best_score == 0.9774
    assert evidence.stage2.subject_count == 15
    assert evidence.stage3.best_mechanism == "less_hierarchical_constraint"
    assert evidence.stage4.best_pair_score > evidence.stage4.best_single_score
    assert evidence.sign_mismatches == ["within_network_stability"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_publication.py::test_build_publication_evidence_collects_stage_metrics -v`

Expected: FAIL with `ModuleNotFoundError` or `ImportError` for `lsd_thesis.publication`.

- [ ] **Step 3: Write minimal implementation**

```python
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class Stage2Evidence:
    initial_score: float
    best_score: float
    subject_count: int
    run_count: int
    dataset_anchor: str
    best_metrics: dict[str, float]
    multi_seed_mean: dict[str, float]
    multi_seed_std: dict[str, float]


@dataclass(slots=True)
class Stage3Evidence:
    best_mechanism: str
    best_strength: float
    best_score: float


@dataclass(slots=True)
class Stage4Evidence:
    best_single_mechanism: str
    best_single_score: float
    best_pair_name: str
    best_pair_score: float


@dataclass(slots=True)
class PublicationEvidence:
    stage1: dict[str, Any]
    stage2: Stage2Evidence
    stage3: Stage3Evidence
    stage4: Stage4Evidence
    empirical_deltas: dict[str, float]
    literature_deltas: dict[str, float]
    condition_models: list[dict[str, Any]]
    multitask_models: list[dict[str, Any]]
    sign_mismatches: list[str]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def build_publication_evidence(repo_root: Path) -> PublicationEvidence:
    stage1 = _read_json(repo_root / "results" / "stage_1" / "stage_1_summary.json")
    stage2_raw = _read_json(repo_root / "results" / "stage_2" / "stage_2_summary.json")
    stage3_raw = _read_json(repo_root / "results" / "stage_3" / "stage_3_summary.json")
    stage4_raw = _read_json(repo_root / "results" / "stage_4" / "stage_4_summary.json")
    empirical = _read_yaml(repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml")["target_deltas"]
    literature = _read_yaml(repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml")["target_deltas"]
    mismatches = [name for name, value in empirical.items() if name in literature and value != 0 and literature[name] != 0 and (value > 0) != (literature[name] > 0)]

    return PublicationEvidence(
        stage1=stage1,
        stage2=Stage2Evidence(
            initial_score=float(stage2_raw["initial_score"]),
            best_score=float(stage2_raw["best_score"]),
            subject_count=int(stage2_raw["empirical_provenance"]["subject_count"]),
            run_count=int(stage2_raw["empirical_provenance"]["run_count"]),
            dataset_anchor=str(stage2_raw["empirical_provenance"]["dataset_anchor"]),
            best_metrics=dict(stage2_raw["best_metrics"]),
            multi_seed_mean=dict(stage2_raw["multi_seed_summary"]["mean_metrics"]),
            multi_seed_std=dict(stage2_raw["multi_seed_summary"]["std_metrics"]),
        ),
        stage3=Stage3Evidence(str(stage3_raw["best_mechanism"]), float(stage3_raw["best_strength"]), float(stage3_raw["best_score"])),
        stage4=Stage4Evidence(
            str(stage4_raw["best_single"]["mechanism"]),
            float(stage4_raw["best_single"]["score"]),
            str(stage4_raw["best_pair"]["mechanism_pair"]),
            float(stage4_raw["best_pair"]["score"]),
        ),
        empirical_deltas={str(k): float(v) for k, v in empirical.items()},
        literature_deltas={str(k): float(v) for k, v in literature.items()},
        condition_models=list(_read_json(repo_root / "results" / "training" / "condition_benchmark" / "comparison_summary.json")["models"]),
        multitask_models=list(_read_json(repo_root / "results" / "training" / "multitask_benchmark" / "comparison_summary.json")["models"]),
        sign_mismatches=mismatches,
    )
```

Update `pyproject.toml`:

```toml
"matplotlib>=3.10.3",
"python-docx>=1.2.0",
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_publication.py::test_build_publication_evidence_collects_stage_metrics -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/lsd_thesis/publication.py tests/test_publication.py
git commit -m "feat: add publication evidence loader"
```

## Task 2: Generate Static Figures And Canonical Narrative Blocks

**Files:**
- Create: `src/lsd_thesis/publication_figures.py`
- Create: `src/lsd_thesis/publication_content.py`
- Test: `tests/test_publication_figures.py`
- Test: `tests/test_publication_content.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path

from lsd_thesis.publication import PublicationEvidence, Stage2Evidence, Stage3Evidence, Stage4Evidence
from lsd_thesis.publication_content import build_defense_outline_markdown, build_thesis_report_markdown
from lsd_thesis.publication_figures import generate_publication_figures


def _sample_evidence() -> PublicationEvidence:
    return PublicationEvidence(
        stage1={"baseline": {"state_entropy": 0.9890, "switching_rate": 0.1471}, "perturbed": {"state_entropy": 0.9976, "switching_rate": 0.2032}},
        stage2=Stage2Evidence(5.2439, 0.9774, 15, 60, "OpenNeuro ds003059", {"within_network_stability": 0.2913}, {"within_network_stability": 0.0962}, {"within_network_stability": 0.0239}),
        stage3=Stage3Evidence("less_hierarchical_constraint", 0.25, 3481.53),
        stage4=Stage4Evidence("less_hierarchical_constraint", 3481.53, "less_hierarchical_constraint+more_stochasticity", 3498.33),
        empirical_deltas={"within_network_stability": 0.0661},
        literature_deltas={"within_network_stability": -0.1},
        condition_models=[{"name": "temporal_cnn", "balanced_accuracy": 0.595}],
        multitask_models=[{"name": "hist_gradient_boosting_multitask", "eigen_r2": 0.2616}],
        sign_mismatches=["within_network_stability"],
    )


def test_generate_publication_figures_writes_pngs_and_manifest(tmp_path: Path) -> None:
    bundle = generate_publication_figures(_sample_evidence(), tmp_path)
    assert (tmp_path / "stage1_metric_shift.png").exists()
    assert (tmp_path / "stage2_fit_robustness.png").exists()
    assert bundle["stage1_metric_shift"]["caption"].startswith("Figure 1.")
    assert "limitation" in bundle["stage2_fit_robustness"]


def test_build_markdown_outputs_include_figures_and_defense_talking_points() -> None:
    bundle = {"stage1_metric_shift": {"path": "output/doc/figures/stage1_metric_shift.png", "caption": "Figure 1. Stage 1 baseline-versus-perturbed entropy shift.", "observation": "Entropy increases.", "interpretation": "The surrogate broadens its state repertoire.", "limitation": "Cross-network mismatch remains."}}
    report = build_thesis_report_markdown(_sample_evidence(), bundle)
    outline = build_defense_outline_markdown(_sample_evidence())
    assert "## Results" in report
    assert "Figure 1. Stage 1 baseline-versus-perturbed entropy shift." in report
    assert "Likely challenge" in outline
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_publication_figures.py::test_generate_publication_figures_writes_pngs_and_manifest -v
uv run pytest tests/test_publication_content.py::test_build_markdown_outputs_include_figures_and_defense_talking_points -v
```

Expected: FAIL with `ModuleNotFoundError` for the new modules.

- [ ] **Step 3: Write minimal implementation**

`src/lsd_thesis/publication_figures.py`

```python
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from lsd_thesis.publication import PublicationEvidence


def _save_chart(path: Path, labels: list[str], values: list[float], title: str, ylabel: str) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(labels, values, color=["#1d4ed8", "#dc2626"][: len(labels)])
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def generate_publication_figures(evidence: PublicationEvidence, output_dir: Path) -> dict[str, dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    _save_chart(output_dir / "stage1_metric_shift.png", ["baseline entropy", "perturbed entropy"], [evidence.stage1["baseline"]["state_entropy"], evidence.stage1["perturbed"]["state_entropy"]], "Stage 1 entropy shift", "Entropy")
    _save_chart(output_dir / "stage2_fit_robustness.png", ["best single", "multi-seed mean"], [evidence.stage2.best_metrics["within_network_stability"], evidence.stage2.multi_seed_mean["within_network_stability"]], "Stage 2 fit robustness", "Within-network stability")
    return {
        "stage1_metric_shift": {
            "path": str(output_dir / "stage1_metric_shift.png"),
            "caption": "Figure 1. Stage 1 baseline-versus-perturbed entropy shift.",
            "observation": "The perturbed regime increases entropy relative to baseline.",
            "interpretation": "The hand-designed perturbation broadens the surrogate state repertoire.",
            "limitation": "Entropy alone does not recover the full altered-state signature.",
        },
        "stage2_fit_robustness": {
            "path": str(output_dir / "stage2_fit_robustness.png"),
            "caption": "Figure 2. Stage 2 best single-seed fit versus multi-seed mean.",
            "observation": "The single best fit materially exceeds the multi-seed average.",
            "interpretation": "The fitter finds a strong seed-specific regime but lacks robustness.",
            "limitation": "The mechanism search should therefore be framed as provisional rather than stable recovery.",
        },
    }
```

`src/lsd_thesis/publication_content.py`

```python
from __future__ import annotations

from lsd_thesis.publication import PublicationEvidence


def build_thesis_report_markdown(evidence: PublicationEvidence, figure_bundle: dict[str, dict[str, str]]) -> str:
    figure = figure_bundle["stage1_metric_shift"]
    return "\n\n".join(
        [
            "# Transparent Surrogate Modeling Of Altered-State-Inspired Macro-Dynamics",
            "Prepared for thesis defense and technical review",
            "[PAGEBREAK]",
            "[TOC]",
            "[PAGEBREAK]",
            "## Results",
            f"![{figure['caption']}]({figure['path']})",
            figure["caption"],
            f"Observation: {figure['observation']}",
            f"Interpretation: {figure['interpretation']}",
            f"Limitation: {figure['limitation']}",
            "## Discussion",
            "The strongest defendable claim is methodological: the repository provides a transparent falsification and hypothesis-ranking environment.",
        ]
    )


def build_defense_outline_markdown(evidence: PublicationEvidence) -> str:
    return "\n".join(
        [
            "# Defense Outline",
            "",
            "## Slide 1: Problem framing",
            "- Talking point: This project builds a surrogate model, not a receptor model.",
            "",
            "## Slide 2: Empirical grounding",
            f"- Talking point: Stage 2 uses {evidence.stage2.subject_count} subjects and {evidence.stage2.run_count} resting runs from {evidence.stage2.dataset_anchor}.",
            "- Likely challenge: Why trust such a coarse eight-module extraction?",
            "- Recommended response: The mapping is presented as a transparent proxy, not a canonical network definition.",
        ]
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run pytest tests/test_publication_figures.py::test_generate_publication_figures_writes_pngs_and_manifest -v
uv run pytest tests/test_publication_content.py::test_build_markdown_outputs_include_figures_and_defense_talking_points -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lsd_thesis/publication_figures.py src/lsd_thesis/publication_content.py tests/test_publication_figures.py tests/test_publication_content.py
git commit -m "feat: add publication figures and narrative builders"
```

## Task 3: Support Figure-Rich DOCX And HTML Output

**Files:**
- Create: `src/lsd_thesis/docx_export.py`
- Create: `src/lsd_thesis/publication_html.py`
- Create: `src/lsd_thesis/templates/thesis_microsite.html`
- Create: `src/lsd_thesis/templates/defense_presentation.html`
- Modify: `scripts/generate_report_docx.py`
- Test: `tests/test_docx_export.py`
- Test: `tests/test_publication_html.py`

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path
from zipfile import ZipFile

from PIL import Image

from lsd_thesis.docx_export import markdown_to_docx
from lsd_thesis.publication_html import render_defense_presentation, render_thesis_microsite


def test_markdown_to_docx_embeds_markdown_images(tmp_path: Path) -> None:
    image_path = tmp_path / "figure.png"
    Image.new("RGB", (120, 80), color="white").save(image_path)
    source = tmp_path / "report.md"
    output = tmp_path / "report.docx"
    source.write_text("\n".join(["# Title", "", "## Results", "", f"![Figure 1. Test figure]({image_path.as_posix()})", "", "Figure 1. Test figure"]), encoding="utf-8")
    markdown_to_docx(source, output)
    with ZipFile(output) as archive:
        media_files = [name for name in archive.namelist() if name.startswith("word/media/")]
    assert media_files


def test_render_thesis_microsite_and_presentation() -> None:
    figure = {"path": "figures/stage1_metric_shift.png", "caption": "Figure 1. Stage 1 baseline-versus-perturbed entropy shift.", "observation": "Entropy increases.", "interpretation": "The surrogate broadens its state repertoire.", "limitation": "Cross-network mismatch remains."}
    report_html = render_thesis_microsite(title="Thesis Microsite", sections=[{"id": "results", "title": "Results", "body": "Stage 1 discussion.", "figures": [figure]}])
    presentation_html = render_defense_presentation(title="Defense Presentation", slides=[{"title": "Main result", "takeaway": "Methodological success, mechanistic failure.", "figure": figure}])
    assert "Results" in report_html
    assert "figures/stage1_metric_shift.png" in report_html
    assert "Main result" in presentation_html
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
uv run pytest tests/test_docx_export.py::test_markdown_to_docx_embeds_markdown_images -v
uv run pytest tests/test_publication_html.py::test_render_thesis_microsite_and_presentation -v
```

Expected: FAIL with `ModuleNotFoundError` for the new modules.

- [ ] **Step 3: Write minimal implementation**

`src/lsd_thesis/docx_export.py`

```python
from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt


IMAGE_PATTERN = re.compile(r"!\[(?P<caption>.*?)\]\((?P<path>.*?)\)")


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.0)
    section.right_margin = Inches(1.0)
    doc.styles["Normal"].font.name = "Times New Roman"
    doc.styles["Normal"].font.size = Pt(12)


def _add_image(doc: Document, image_path: Path, caption: str) -> None:
    paragraph = doc.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.add_run().add_picture(str(image_path), width=Inches(6.0))
    caption_para = doc.add_paragraph(caption)
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER


def markdown_to_docx(source_path: Path, output_path: Path) -> None:
    doc = Document()
    configure_document(doc)
    for raw_line in source_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped:
            continue
        match = IMAGE_PATTERN.fullmatch(stripped)
        if match:
            _add_image(doc, Path(match.group("path")), match.group("caption"))
        elif stripped.startswith("# "):
            doc.add_heading(stripped[2:], level=0)
        elif stripped.startswith("## "):
            doc.add_heading(stripped[3:], level=1)
        else:
            doc.add_paragraph(stripped)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
```

`src/lsd_thesis/publication_html.py`

```python
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATE_ROOT = Path(__file__).resolve().parent / "templates"
ENV = Environment(loader=FileSystemLoader(str(TEMPLATE_ROOT)), autoescape=select_autoescape(["html"]))


def render_thesis_microsite(*, title: str, sections: list[dict[str, object]]) -> str:
    return ENV.get_template("thesis_microsite.html").render(title=title, sections=sections)


def render_defense_presentation(*, title: str, slides: list[dict[str, object]]) -> str:
    return ENV.get_template("defense_presentation.html").render(title=title, slides=slides)
```

Template starter for `src/lsd_thesis/templates/thesis_microsite.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  <style>
    body { font-family: Georgia, serif; margin: 0; color: #18212b; background: #f6f2ea; }
    nav { position: sticky; top: 0; background: #18212b; color: white; padding: 12px 24px; }
    main { max-width: 960px; margin: 0 auto; padding: 40px 24px 96px; }
    figure { background: white; padding: 16px; border: 1px solid #d8d0c2; }
    img { max-width: 100%; display: block; margin: 0 auto 12px; }
  </style>
</head>
<body>
  <nav>{{ title }}</nav>
  <main>
    {% for section in sections %}
    <section id="{{ section.id }}">
      <h2>{{ section.title }}</h2>
      <p>{{ section.body }}</p>
      {% for figure in section.figures %}
      <figure>
        <img src="{{ figure.path }}" alt="{{ figure.caption }}">
        <figcaption><strong>{{ figure.caption }}</strong></figcaption>
        <p>Observation: {{ figure.observation }}</p>
        <p>Interpretation: {{ figure.interpretation }}</p>
        <p>Limitation: {{ figure.limitation }}</p>
      </figure>
      {% endfor %}
    </section>
    {% endfor %}
  </main>
</body>
</html>
```

Template starter for `src/lsd_thesis/templates/defense_presentation.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{{ title }}</title>
  <style>
    body { font-family: "Segoe UI", sans-serif; margin: 0; background: #101820; color: #f4efe6; }
    .slide { min-height: 100vh; display: grid; grid-template-columns: 1.2fr 1fr; gap: 32px; padding: 48px; box-sizing: border-box; }
    .visual img { max-width: 100%; background: white; padding: 12px; }
  </style>
</head>
<body>
  {% for slide in slides %}
  <section class="slide">
    <div class="visual">
      <img src="{{ slide.figure.path }}" alt="{{ slide.figure.caption }}">
      <p>{{ slide.figure.caption }}</p>
    </div>
    <div>
      <h1>{{ slide.title }}</h1>
      <p>{{ slide.takeaway }}</p>
      <p>Observation: {{ slide.figure.observation }}</p>
      <p>Interpretation: {{ slide.figure.interpretation }}</p>
      <p>Limitation: {{ slide.figure.limitation }}</p>
    </div>
  </section>
  {% endfor %}
</body>
</html>
```

Replace `scripts/generate_report_docx.py` with a thin wrapper:

```python
from __future__ import annotations

import sys
from pathlib import Path

from lsd_thesis.docx_export import markdown_to_docx


def main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("Usage: python scripts/generate_report_docx.py <source.md> <output.docx>")
    markdown_to_docx(Path(sys.argv[1]), Path(sys.argv[2]))
    print(Path(sys.argv[2]))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run:

```bash
uv run pytest tests/test_docx_export.py::test_markdown_to_docx_embeds_markdown_images -v
uv run pytest tests/test_publication_html.py::test_render_thesis_microsite_and_presentation -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/lsd_thesis/docx_export.py src/lsd_thesis/publication_html.py src/lsd_thesis/templates/thesis_microsite.html src/lsd_thesis/templates/defense_presentation.html scripts/generate_report_docx.py tests/test_docx_export.py tests/test_publication_html.py
git commit -m "feat: support publication docx and html outputs"
```

## Task 4: Orchestrate End-To-End Build And Expose Output Links

**Files:**
- Create: `scripts/build_publication_package.py`
- Modify: `src/lsd_thesis/web/app.py`
- Modify: `tests/test_web.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path

from lsd_thesis.web.app import _artifact_links


def test_artifact_links_include_publication_outputs(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "output" / "doc").mkdir(parents=True)
    (repo_root / "output" / "doc" / "thesis_report_revised.pdf").write_text("pdf", encoding="utf-8")
    (repo_root / "output" / "doc" / "thesis_microsite.html").write_text("<html></html>", encoding="utf-8")
    (repo_root / "output" / "doc" / "defense_presentation.html").write_text("<html></html>", encoding="utf-8")
    links = _artifact_links(repo_root)
    labels = [item["label"] for item in links["reports"]]
    assert "Thesis Report Revised" in labels
    assert "Thesis Microsite" in labels
    assert "Defense Presentation" in labels
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_web.py::test_artifact_links_include_publication_outputs -v`

Expected: FAIL because `_artifact_links` does not include `output/doc` artifacts yet.

- [ ] **Step 3: Write minimal implementation**

`scripts/build_publication_package.py`

```python
from __future__ import annotations

from pathlib import Path

from lsd_thesis.docx_export import markdown_to_docx
from lsd_thesis.publication import build_publication_evidence
from lsd_thesis.publication_content import build_defense_outline_markdown, build_thesis_report_markdown
from lsd_thesis.publication_figures import generate_publication_figures
from lsd_thesis.publication_html import render_defense_presentation, render_thesis_microsite


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    output_root = repo_root / "output" / "doc"
    figure_root = output_root / "figures"
    output_root.mkdir(parents=True, exist_ok=True)

    evidence = build_publication_evidence(repo_root)
    bundle = generate_publication_figures(evidence, figure_root)

    report_md = output_root / "thesis_report_revised.md"
    outline_md = output_root / "defense_outline.md"
    report_docx = output_root / "thesis_report_revised.docx"
    outline_docx = output_root / "defense_outline.docx"

    report_md.write_text(build_thesis_report_markdown(evidence, bundle), encoding="utf-8")
    outline_md.write_text(build_defense_outline_markdown(evidence), encoding="utf-8")
    markdown_to_docx(report_md, report_docx)
    markdown_to_docx(outline_md, outline_docx)

    microsite = render_thesis_microsite(title="Transparent Surrogate Modeling Of Altered-State-Inspired Macro-Dynamics", sections=[{"id": "results", "title": "Results", "body": "Stage-linked figures and discussion generated from saved artifacts.", "figures": list(bundle.values())}])
    presentation = render_defense_presentation(title="Thesis Defense Presentation", slides=[{"title": "Central claim", "takeaway": "Methodological success does not imply mechanistic confirmation.", "figure": next(iter(bundle.values()))}])
    (output_root / "thesis_microsite.html").write_text(microsite, encoding="utf-8")
    (output_root / "defense_presentation.html").write_text(presentation, encoding="utf-8")
```

Extend `_artifact_links` in `src/lsd_thesis/web/app.py`

```python
report_paths = [
    repo_root / "docs" / "stage_reports" / "stage_2.md",
    repo_root / "docs" / "stage_reports" / "stage_3.md",
    repo_root / "docs" / "stage_reports" / "stage_4.md",
    repo_root / "output" / "doc" / "thesis_report_revised.pdf",
    repo_root / "output" / "doc" / "thesis_microsite.html",
    repo_root / "output" / "doc" / "defense_presentation.html",
]
```

Add a short `README.md` section

```md
## Publication Outputs

Generate the thesis publication package with:

```bash
uv run python scripts/build_publication_package.py
```

Outputs are written to `output/doc/`.
```

- [ ] **Step 4: Run focused verification and build**

Run:

```bash
uv run pytest tests/test_web.py::test_artifact_links_include_publication_outputs -v
uv run python scripts/build_publication_package.py
uv run ruff check src/lsd_thesis/publication.py src/lsd_thesis/publication_figures.py src/lsd_thesis/publication_content.py src/lsd_thesis/publication_html.py src/lsd_thesis/docx_export.py scripts/build_publication_package.py scripts/generate_report_docx.py
```

Expected:
- PASS on the focused test
- generated files under `output/doc/`
- clean ruff output

Then export PDF on this Windows workstation:

```powershell
@'
from pathlib import Path
from win32com.client import Dispatch

root = Path(r"D:\LSD_Thesis\output\doc")
word = Dispatch("Word.Application")
word.Visible = False
doc = word.Documents.Open(str(root / "thesis_report_revised.docx"))
doc.Fields.Update()
doc.SaveAs(str(root / "thesis_report_revised.pdf"), FileFormat=17)
doc.Close()
word.Quit()
'@ | python -
```

Manual check:
- `output/doc/thesis_report_revised.pdf`
- `output/doc/thesis_microsite.html`
- `output/doc/defense_presentation.html`

- [ ] **Step 5: Commit**

```bash
git add scripts/build_publication_package.py src/lsd_thesis/web/app.py tests/test_web.py README.md output/doc
git commit -m "docs: publish thesis report package"
```

## Self-Review

### Spec coverage

- Revised report: Tasks 2 to 4.
- Figure pack with explanations and discussion: Task 2.
- Microsite HTML: Tasks 3 and 4.
- Defense presentation HTML: Tasks 3 and 4.
- Defense outline: Tasks 2 and 4.
- Dashboard-accessible links: Task 4.

### Placeholder scan

- No placeholder markers remain.
- Every code-writing step includes exact file paths and executable starter code.

### Type consistency

- `PublicationEvidence` and stage dataclasses are introduced in Task 1 and reused consistently in later tasks.
- `markdown_to_docx` is defined in Task 3 and reused in Task 4.
- Figure bundle keys are reused consistently between the figure generator, content builder, and HTML renderer.
