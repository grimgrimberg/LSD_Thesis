from __future__ import annotations

import importlib.util
from pathlib import Path

from lsd_thesis.publication import PublicationEvidence, Stage2Evidence, Stage3Evidence, Stage4Evidence
from lsd_thesis.publication_content import build_thesis_report_markdown
from lsd_thesis.publication_figures import PublicationFigure
from lsd_thesis.publication_pptx import build_defense_pptx_slides


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


def _load_build_publication_package_module():
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "build_publication_package.py"
    spec = importlib.util.spec_from_file_location("build_publication_package", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def test_build_defense_pptx_slides_groups_long_form_report_into_presentable_deck(
    tmp_path: Path,
) -> None:
    evidence = _build_sample_publication_evidence()
    report_markdown = build_thesis_report_markdown(evidence, _build_sample_figure_bundle(tmp_path))

    slides = build_defense_pptx_slides(report_markdown)

    assert len(slides) == 14
    assert slides[0]["title"] == "Transparent Surrogate Modeling of Altered-State-Inspired Macro-Dynamics"
    assert slides[1]["title"] == "Scope and Claim Boundaries"
    assert slides[7]["title"] == "Stage 2 Empirical Bridge and Fit"
    assert slides[-1]["title"] == "Defendable Conclusion"


def test_build_defense_pptx_slides_preserves_key_figures_and_mechanism_language(
    tmp_path: Path,
) -> None:
    evidence = _build_sample_publication_evidence()
    report_markdown = build_thesis_report_markdown(evidence, _build_sample_figure_bundle(tmp_path))

    slides = build_defense_pptx_slides(report_markdown)
    stage1_slide = next(slide for slide in slides if slide["title"] == "Stage 1 Synthetic Shift")
    stage2_slide = next(slide for slide in slides if slide["title"] == "Stage 2 Empirical Bridge and Fit")
    stage3_slide = next(slide for slide in slides if slide["title"] == "Stage 3 Mechanism Ranking")

    assert stage1_slide["image_path"] == "figures/stage1_metric_shift.png"
    assert stage2_slide["image_path"] == "figures/stage2_fit_robustness.png"
    assert any("less_hierarchical_constraint" in bullet for bullet in stage3_slide["bullets"])


def test_build_publication_package_emits_pptx_artifact(tmp_path: Path) -> None:
    module = _load_build_publication_package_module()
    evidence = _build_sample_publication_evidence()
    figure_bundle = _build_sample_figure_bundle(tmp_path)
    captured: dict[str, object] = {}

    module.build_publication_evidence = lambda repo_root: evidence
    module.generate_publication_figures = lambda evidence, output_dir: figure_bundle
    module.markdown_to_docx = lambda src, dst: dst.write_text("docx stub", encoding="utf-8")

    def _fake_build_defense_presentation_pptx(repo_root, slides, output_path):
        captured["slides"] = slides
        output_path.write_bytes(b"pptx")
        return output_path

    module.build_defense_presentation_pptx = _fake_build_defense_presentation_pptx

    outputs = module.build_publication_package(tmp_path)

    assert outputs["defense_presentation_pptx"].name == "defense_presentation.pptx"
    assert outputs["defense_presentation_pptx"].read_bytes() == b"pptx"
    assert isinstance(captured["slides"], list)
    assert len(captured["slides"]) == 14
