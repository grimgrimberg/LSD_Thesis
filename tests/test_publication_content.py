from __future__ import annotations

from pathlib import Path

from lsd_thesis.publication import PublicationEvidence, Stage2Evidence, Stage3Evidence, Stage4Evidence, SubjectValidationEvidence
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
    assert "currently passes its local verification suite" not in markdown
    assert "tests pass, static typing is clean, linting passes" not in markdown
    assert "full empirical cohort" not in markdown


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
    assert "best-scoring perturbation family is `less_hierarchical_constraint` at strength `0.25`" in markdown
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


def test_build_thesis_report_markdown_derives_stage4_scores_from_evidence(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage4 = Stage4Evidence(
        best_single_mechanism="single_proxy",
        best_single_score=7.5,
        best_pair_name="pair_proxy",
        best_pair_score=6.25,
    )
    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert "best single mechanism: `single_proxy`" in markdown
    assert "best single score: `7.5000`" in markdown
    assert "best pairwise mechanism: `pair_proxy`" in markdown
    assert "best pairwise score: `6.2500`" in markdown
    assert "outperformed the best single mechanism" in markdown
    assert "3481.5367" not in markdown
    assert "3498.3309" not in markdown
    assert "57` tests passed" not in markdown


def test_build_thesis_report_markdown_avoids_fixed_validation_claims(tmp_path: Path) -> None:
    evidence = _build_sample_publication_evidence()
    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert "57 tests passed" not in markdown
    assert "On 2026-04-15 the local checks passed" not in markdown
    assert "best score comes from a single stochastic realization" not in markdown
    assert "intentionally avoids embedding a fixed test count or dated validation claim" in markdown
    assert "Subject-disjoint held-out validation has not yet been configured or performed" in markdown


def test_build_thesis_report_markdown_discloses_configured_split_without_claiming_completion(
    tmp_path: Path,
) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage2.validation_boundary = SubjectValidationEvidence(
        configured=True,
        completed=False,
        split_strategy="subject_disjoint",
        selection_subject_count=12,
        validation_subject_count=3,
        overlap_count=0,
        claim_guardrail="Subject-disjoint split is configured, but held-out validation has not yet been completed.",
    )
    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert "subject-disjoint split is configured" in markdown
    assert "not yet been completed" in markdown
    assert "subject-disjoint held-out validation has been completed" not in markdown


def test_build_thesis_report_markdown_discloses_candidate_split_without_approval(
    tmp_path: Path,
) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.stage2.validation_boundary = SubjectValidationEvidence(
        configured=True,
        completed=False,
        approval_status="candidate",
        split_strategy="subject_disjoint",
        selection_subject_count=12,
        validation_subject_count=3,
        overlap_count=0,
        claim_guardrail="Candidate split is configured, but held-out validation has not yet been completed.",
    )
    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert "candidate subject-disjoint split is prepared" in markdown.lower()
    assert "not approved" in markdown
    assert "subject-disjoint held-out validation has been completed" not in markdown


def test_build_thesis_report_markdown_discloses_completed_cv5_internal_validation(
    tmp_path: Path,
) -> None:
    evidence = _build_sample_publication_evidence()
    evidence.cv5_validation = {
        "held_out_validation_completed": True,
        "completed_folds": 5,
        "total_folds": 5,
        "total_subjects": 15,
        "validation_claim_scope": "preliminary_internal_subject_disjoint_cv5",
        "source_manifest_path": "output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json",
        "aggregate_path": "output/validation/cv5_subject_disjoint/results/cv5_aggregate_validation.json",
        "run_parameters": {
            "run_command": (
                "uv run python scripts/run_cv5_validation.py --manifest "
                "output/validation/cv5_subject_disjoint/approved/subject_split_cv5_manifest_approved.json "
                "--output-dir output/validation/cv5_subject_disjoint/results --fit-iterations 64 --seed 11"
            ),
        },
        "aggregate_metrics": {
            "score_mean": {"mean": 0.42, "std": 0.03},
            "sign_agreement_fraction": {"mean": 0.675, "std": 0.19},
            "selected_mechanism_counts": {"more_cross_talk": 5},
            "selected_strength_counts": {"0.1": 5},
        },
        "per_fold_metrics": [
            {"fold_id": "fold_01", "score_mean": 0.25, "sign_agreement_fraction": 0.5},
            {"fold_id": "fold_02", "score_mean": 0.62, "sign_agreement_fraction": 0.875},
        ],
    }
    figure_bundle = generate_publication_figures(evidence, tmp_path / "figures")

    markdown = build_thesis_report_markdown(evidence, figure_bundle)

    assert "Approved preliminary five-fold subject-disjoint internal validation completed across 5/5 folds" in markdown
    assert "not external or clinical validation" in markdown
    assert "n=3 held-out subjects per fold" in markdown
    assert "No subject-level motion/FD/DVARS/confound/censoring stratification was available" in markdown
    assert "the aggregate artifact is the authoritative completion record" in markdown
    assert "| Fold-averaged delta mismatch score | 0.4200 (fold SD 0.0300) |" in markdown
    assert "| Held-out score range | 0.2500 to 0.6200 |" in markdown
    assert "| Fold-averaged target-sign agreement | 0.6750 (fold SD 0.1900) |" in markdown
    assert "fold standard deviation is not a confidence interval" in markdown
    assert "output/validation/cv5_subject_disjoint/results/cv5_aggregate_validation.json" in markdown
    assert "subject-disjoint held-out validation has been completed" not in markdown
