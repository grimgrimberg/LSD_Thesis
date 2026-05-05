from __future__ import annotations

from pathlib import Path

from lsd_thesis.publication import PublicationEvidence, Stage2Evidence, Stage3Evidence, Stage4Evidence
from lsd_thesis.publication_content import build_defense_outline_markdown, build_thesis_report_markdown
from lsd_thesis.publication_figures import PublicationFigure, generate_publication_figures


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


def test_build_thesis_report_markdown_builds_long_form_thesis_structure(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert markdown.startswith("# Transparent Surrogate Modeling of Altered-State-Inspired Macro-Dynamics")
    assert "## Abstract" in markdown
    assert "## 1. Introduction and Problem Statement" in markdown
    assert "## 4. Repository Architecture and Staged Workflow" in markdown
    assert "## 10. Stage 2: Empirical Bridge and Sober-Regime Fitting" in markdown
    assert "## 18. Defendable Thesis Claims and Claims to Avoid" in markdown
    assert "## 20. Conclusion" in markdown
    assert "](figures/stage1_metric_shift.png)" in markdown
    assert "](figures/stage2_fit_robustness.png)" in markdown
    assert str(figure_bundle["stage1_metric_shift"].path) not in markdown
    assert "*Limitation:" in markdown
    assert "These are surrogate macro-dynamics only." in markdown
    assert evidence.stage2.dataset_anchor in markdown
    assert "The model is a surrogate." in markdown
    assert "It does not show that LSD has been mechanistically simulated." in markdown
    assert "The central conclusion is not that psychedelic whole-brain dynamics have been explained." in markdown


def test_build_thesis_report_markdown_uses_figures_contract_for_absolute_paths(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    figure_bundle = {
        "stage1_metric_shift": PublicationFigure(
            figure_id="stage1_metric_shift",
            path=tmp_path / "publication_assets" / "stage1_metric_shift.png",
            caption="Stage 1 compares baseline and perturbed proxy values for entropy and switching rate.",
            limitations="These are surrogate macro-dynamics only.",
        ),
        "stage2_fit_robustness": PublicationFigure(
            figure_id="stage2_fit_robustness",
            path=tmp_path / "publication_assets" / "stage2_fit_robustness.png",
            caption="Stage 2 compares the initial objective with a later comparison score and summarizes limited repeatability evidence.",
            limitations="This figure summarizes a cached benchmark anchored to a synthetic benchmark anchor.",
        ),
    }

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert "](figures/stage1_metric_shift.png)" in markdown
    assert "](figures/stage2_fit_robustness.png)" in markdown
    assert "### Stage 1 synthetic shift snapshot" in markdown
    assert "### Stage 2 fit and robustness snapshot" in markdown
    assert "best observed fit" not in markdown
    assert "leading fit" not in markdown
    assert "synthetic benchmark anchor" in markdown


def test_build_thesis_report_markdown_threads_current_evidence_into_long_form_sections(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert "fifteen paired subjects and sixty total resting runs" in markdown
    assert "best-ranked perturbation mechanism is `less_hierarchical_constraint` at strength `0.25`" in markdown
    assert "`less_hierarchical_constraint+more_stochasticity`" in markdown
    assert "sign mismatches remain for: `within_network_stability`." in markdown
    assert (
        "Stage 2 objective changed from 5.244 to 0.977 (decreased); lower scores are better. "
        "The selected score comes from the optimization step."
    ) in markdown


def test_build_defense_outline_markdown_includes_talking_points_and_challenge() -> None:
    evidence = _build_sample_publication_evidence()

    markdown = build_defense_outline_markdown(evidence)

    assert "talking points" in markdown.lower()
    assert "Likely challenge" in markdown
    assert "surrogate model of altered-state-inspired macro-dynamics" in markdown
    assert "not receptor mechanisms or subjective reports" in markdown
    assert "The repository is strongest when it makes narrow, testable macro-dynamics claims." in markdown
    assert "macro-dynamics level" in markdown
    assert "leading fit" not in markdown.lower()
    assert "improves" not in markdown.lower()


def test_build_publication_content_handles_reversed_stage2_scores(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage2.initial_score = 0.5
    evidence.stage2.best_score = 1.25
    evidence.stage2.dataset_anchor = "Custom benchmark anchor"

    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    report_markdown = build_thesis_report_markdown(evidence, figure_bundle)
    outline_markdown = build_defense_outline_markdown(evidence)

    expected_sentence = (
        "Stage 2 objective changed from 0.500 to 1.250 (increased); lower scores are better. "
        "The selected score comes from the optimization step."
    )
    assert expected_sentence in report_markdown
    assert expected_sentence in outline_markdown
    assert "improved" not in report_markdown.lower()
    assert "improves" not in outline_markdown.lower()
    assert "leading fit" not in outline_markdown.lower()
    assert "Custom benchmark anchor" in report_markdown
    assert "Custom benchmark anchor" in outline_markdown
