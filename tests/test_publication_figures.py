from __future__ import annotations

from pathlib import Path

import pytest

from lsd_thesis.publication import PublicationEvidence, Stage2Evidence, Stage3Evidence, Stage4Evidence
from lsd_thesis.publication_figures import generate_publication_figures


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


def test_generate_publication_figures_writes_expected_pngs(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    output_dir = tmp_path / "figures"

    figure_bundle = generate_publication_figures(evidence, output_dir)

    assert (output_dir / "stage1_metric_shift.png").exists()
    assert (output_dir / "stage2_fit_robustness.png").exists()
    assert set(figure_bundle) == {"stage1_metric_shift", "stage2_fit_robustness"}
    assert "receptor-level realism" in figure_bundle["stage1_metric_shift"].limitations
    assert "generalization" in figure_bundle["stage2_fit_robustness"].limitations
    assert "selected score from the optimization step" in figure_bundle["stage2_fit_robustness"].caption
    assert "best observed fit" not in figure_bundle["stage2_fit_robustness"].caption


def test_generate_publication_figures_rejects_incomplete_stage1_metrics(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage1 = {"baseline": {"state_entropy": 0.989, "switching_rate": 0.118}}

    with pytest.raises(ValueError, match="baseline and perturbed"):
        generate_publication_figures(evidence, tmp_path / "figures")


def test_generate_publication_figures_rejects_missing_stage1_metric(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage1 = {
        "baseline": {"state_entropy": 0.989, "switching_rate": 0.118},
        "perturbed": {"state_entropy": 1.012},
    }

    with pytest.raises(ValueError, match="Missing stage1 metric 'switching_rate'"):
        generate_publication_figures(evidence, tmp_path / "figures")


def test_generate_publication_figures_uses_neutral_captions_for_reversed_values(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage1 = {
        "baseline": {"state_entropy": 1.012, "switching_rate": 0.164},
        "perturbed": {"state_entropy": 0.989, "switching_rate": 0.118},
    }
    evidence.stage2.initial_score = 0.5
    evidence.stage2.best_score = 1.25

    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    stage1_caption = figure_bundle["stage1_metric_shift"].caption.lower()
    stage2_caption = figure_bundle["stage2_fit_robustness"].caption.lower()
    assert "compare" in stage1_caption
    assert "baseline and perturbed proxy values" in stage1_caption
    assert "drop" not in stage1_caption
    assert "raise" not in stage1_caption
    assert "compare" in stage2_caption
    assert "initial objective with the selected score from the optimization step" in stage2_caption
    assert "drop" not in stage2_caption
    assert "increase" not in stage2_caption


def test_generate_publication_figures_reports_stage2_direction_from_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage2.initial_score = 0.5
    evidence.stage2.best_score = 1.25

    captured: dict[str, object] = {}

    def fake_save_figure(fig: object, path: Path) -> None:
        captured[path.name] = fig

    from lsd_thesis import publication_figures as publication_figures_module

    monkeypatch.setattr(publication_figures_module, "_save_figure", fake_save_figure)

    publication_figures_module.generate_publication_figures(evidence, tmp_path / "figures")

    stage2_figure = captured["stage2_fit_robustness.png"]
    axes = stage2_figure.axes[0]
    annotation_text = "\n".join(text.get_text() for text in axes.texts)
    xtick_labels = [tick.get_text() for tick in axes.get_xticklabels()]
    assert axes.get_title() == "Stage 2 objective comparison"
    assert xtick_labels == ["Initial", "Selected score"]
    assert "Change: increased by 0.75" in annotation_text
    assert "Lower scores are better." not in annotation_text
    assert "Improvement:" not in annotation_text
    assert "Best" not in xtick_labels


def test_generate_publication_figures_uses_neutral_captions_for_equal_stage1_values(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage1 = {
        "baseline": {"state_entropy": 1.0, "switching_rate": 0.2},
        "perturbed": {"state_entropy": 1.0, "switching_rate": 0.2},
    }

    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    caption = figure_bundle["stage1_metric_shift"].caption.lower()
    assert "compare" in caption
    assert "increase" not in caption
    assert "decrease" not in caption
