from __future__ import annotations

import importlib.util
from html.parser import HTMLParser
from pathlib import Path

from lsd_thesis.publication import PublicationEvidence, Stage2Evidence, Stage3Evidence, Stage4Evidence
from lsd_thesis.publication_content import build_thesis_report_markdown
from lsd_thesis.publication_figures import PublicationFigure
from lsd_thesis.publication_html import (
    build_defense_presentation_slides,
    build_thesis_microsite_sections,
    render_defense_presentation,
    render_thesis_microsite,
)

_SAMPLE_REPORT = """# Transparent Surrogate Modeling of Altered-State-Inspired Macro-Dynamics

Prepared for thesis defense and technical review.

[PAGEBREAK]

[TOC]

## Executive Summary

This section includes <markup> and `code` samples.

- First evidence bullet
- Second evidence bullet

## 9. Stage 1: Baseline Versus Altered-State-Inspired Synthetic Dynamics

### Stage 1 synthetic shift snapshot

![Stage "1" & shift](figures/stage 1 metric shift.png)

*Figure: Stage 1 figure caption*

*Limitation: Example limitation.*

Stage 1 paragraph after the figure.

## 10. Stage 2: Empirical Bridge and Sober-Regime Fitting

Stage 2 objective changed from 0.500 to 1.250 (increased); lower scores are better.
"""


def _load_build_publication_package_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_publication_package.py"
    spec = importlib.util.spec_from_file_location("build_publication_package", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_sample_publication_evidence() -> PublicationEvidence:
    return PublicationEvidence(
        stage1={
            "baseline": {"state_entropy": 0.989, "switching_rate": 0.118},
            "perturbed": {"state_entropy": 1.012, "switching_rate": 0.164},
        },
        stage2=Stage2Evidence(
            initial_score=5.2439,
            best_score=0.9774,
            subject_count=15,
            run_count=60,
            dataset_anchor="OpenNeuro ds003059 placebo resting-state summary",
            best_metrics={
                "within_network_stability": 0.2913,
                "cross_network_communication": 0.1014,
            },
            multi_seed_mean={
                "within_network_stability": 0.0962,
                "cross_network_communication": 0.0420,
            },
            multi_seed_std={
                "within_network_stability": 0.0239,
                "cross_network_communication": 0.0256,
            },
        ),
        stage3=Stage3Evidence(
            best_mechanism="less_hierarchical_constraint",
            best_strength=0.25,
            best_score=3481.5367,
        ),
        stage4=Stage4Evidence(
            best_single_mechanism="less_hierarchical_constraint",
            best_single_score=3481.5367,
            best_pair_name="less_hierarchical_constraint+more_stochasticity",
            best_pair_score=3498.3309,
        ),
        empirical_deltas={
            "within_network_stability": 0.0661,
            "cross_network_communication": 0.0741,
        },
        literature_deltas={
            "within_network_stability": -0.30,
            "cross_network_communication": 0.25,
        },
        condition_models=[{"name": "temporal_cnn", "balanced_accuracy": 0.595}],
        multitask_models=[{"name": "hist_gradient_boosting_multitask", "eigen_r2": 0.2616}],
        sign_mismatches=["within_network_stability"],
    )


def _build_sample_figure_bundle(tmp_path: Path) -> dict[str, PublicationFigure]:
    return {
        "stage1_metric_shift": PublicationFigure(
            figure_id="stage1_metric_shift",
            path=tmp_path / "stage1_metric_shift.png",
            caption="Stage 1 compares baseline and perturbed proxy values for entropy and switching rate.",
            limitations=(
                "These are surrogate macro-dynamics only. They do not claim receptor-level realism, "
                "subjective experience, or direct biological measurement."
            ),
        ),
        "stage2_fit_robustness": PublicationFigure(
            figure_id="stage2_fit_robustness",
            path=tmp_path / "stage2_fit_robustness.png",
            caption=(
                "Stage 2 compares the initial objective with the selected score from the optimization step and summarizes limited repeatability evidence."
            ),
            limitations=(
                "This figure summarizes a cached benchmark anchored to OpenNeuro ds003059 placebo resting-state summary. "
                "It is evidence of fit quality and run-to-run consistency, not a proof of generalization."
            ),
        ),
    }


class _FirstImageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.first_image_attrs: dict[str, str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != "img" or self.first_image_attrs is not None:
            return
        self.first_image_attrs = {name: value or "" for name, value in attrs}


def test_build_thesis_microsite_sections_parse_long_form_report_blocks() -> None:
    sections = build_thesis_microsite_sections(_SAMPLE_REPORT)

    assert len(sections) == 3
    assert sections[0]["title"] == "Executive Summary"
    assert sections[0]["summary"] == "This section includes <markup> and code samples."
    assert "First evidence bullet" in sections[0]["body_html"]
    assert sections[1]["figure_count"] == 1
    assert "Stage 1 figure caption" in sections[1]["body_html"]
    assert "Example limitation." in sections[1]["body_html"]


def test_render_thesis_microsite_includes_toc_escaped_markup_and_image_paths() -> None:
    sections = build_thesis_microsite_sections(_SAMPLE_REPORT)
    html = render_thesis_microsite("Thesis Microsite", sections)

    assert "<title>Thesis Microsite</title>" in html
    assert "Contents" in html
    assert "Executive Summary" in html
    assert "10. Stage 2: Empirical Bridge and Sober-Regime Fitting" in html
    assert "&lt;markup&gt;" in html
    assert "<code>code</code>" in html
    parser = _FirstImageParser()
    parser.feed(html)
    assert parser.first_image_attrs is not None
    assert parser.first_image_attrs["src"] == "figures/stage 1 metric shift.png"
    assert parser.first_image_attrs["alt"] == 'Stage "1" & shift'


def test_build_defense_presentation_slides_are_derived_from_long_form_report() -> None:
    slides = build_defense_presentation_slides(_SAMPLE_REPORT)
    html = render_defense_presentation("Defense Deck", slides)

    assert len(slides) == 3
    assert slides[0]["title"] == "Executive Summary"
    assert "Derived from the long-form report section 1 of 3." in html
    assert "Stage 2 objective changed from 0.500 to 1.250" in html
    assert "Stage 1 figure caption" in html


def test_build_defense_presentation_slides_preserve_evidence_derived_stage_content(
    tmp_path: Path,
) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage2.initial_score = 0.5
    evidence.stage2.best_score = 1.25
    evidence.stage3.best_mechanism = "more_cross_talk"
    evidence.stage4.best_pair_name = "more_cross_talk+more_stochasticity"

    report_markdown = build_thesis_report_markdown(evidence, _build_sample_figure_bundle(tmp_path))
    slides = build_defense_presentation_slides(report_markdown)

    stage2_slide = next(slide for slide in slides if slide["title"].startswith("10. Stage 2"))
    stage3_slide = next(slide for slide in slides if slide["title"].startswith("11. Stage 3"))
    stage4_slide = next(slide for slide in slides if slide["title"].startswith("12. Stage 4"))

    assert "0.500" in stage2_slide["takeaway"]
    assert "1.250" in stage2_slide["takeaway"]
    assert "more_cross_talk" in stage3_slide["takeaway"]
    assert "more_cross_talk+more_stochasticity" in stage4_slide["takeaway"]


def test_build_publication_package_wires_html_from_report_markdown(tmp_path: Path) -> None:
    module = _load_build_publication_package_module()
    evidence = _build_sample_publication_evidence()
    figure_bundle = _build_sample_figure_bundle(tmp_path)
    custom_report = """# Transparent Surrogate Modeling of Altered-State-Inspired Macro-Dynamics

## Executive Summary

This report includes <markup> to prove escaping.

## 10. Stage 2: Empirical Bridge and Sober-Regime Fitting

Stage 2 text.
"""

    module.build_publication_evidence = lambda repo_root: evidence
    module.generate_publication_figures = lambda evidence, output_dir: figure_bundle
    module.build_thesis_report_markdown = lambda evidence, figure_bundle: custom_report
    module.build_defense_outline_markdown = lambda evidence: "# Defense Outline\n"
    module.markdown_to_docx = lambda src, dst: dst.write_text("docx stub", encoding="utf-8")
    module.build_defense_pptx_slides = lambda report_markdown: []

    def _fake_build_defense_presentation_pptx(repo_root, slides, output_path):
        output_path.write_bytes(b"pptx")
        return output_path

    module.build_defense_presentation_pptx = _fake_build_defense_presentation_pptx

    outputs = module.build_publication_package(tmp_path)
    microsite_html = outputs["thesis_microsite_html"].read_text(encoding="utf-8")
    deck_html = outputs["defense_presentation_html"].read_text(encoding="utf-8")

    assert "&lt;markup&gt;" in microsite_html
    assert "Executive Summary" in microsite_html
    assert "10. Stage 2: Empirical Bridge and Sober-Regime Fitting" in microsite_html
    assert "Derived from the long-form report section 2 of 2." in deck_html
    assert "Stage 2 text." in deck_html
