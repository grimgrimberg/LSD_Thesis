from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from lsd_thesis.publication import build_publication_evidence


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_yaml(path: Path, payload: object) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _write_publication_fixture(
    repo_root: Path,
    *,
    stage2_provenance: dict[str, object] | None = None,
    empirical_validation_boundary: dict[str, object] | None = None,
    stage3_payload: object | None = None,
    stage4_payload: object | None = None,
    condition_models: object | None = None,
    empirical_target_deltas: dict[str, object] | None = None,
    literature_target_deltas: dict[str, object] | None = None,
) -> None:
    (repo_root / "results" / "stage_1").mkdir(parents=True)
    (repo_root / "results" / "stage_2").mkdir(parents=True)
    (repo_root / "results" / "stage_3").mkdir(parents=True)
    (repo_root / "results" / "stage_4").mkdir(parents=True)
    (repo_root / "results" / "training" / "condition_benchmark").mkdir(parents=True)
    (repo_root / "results" / "training" / "multitask_benchmark").mkdir(parents=True)
    (repo_root / "configs" / "targets").mkdir(parents=True)

    _write_json(
        repo_root / "results" / "stage_1" / "stage_1_summary.json",
        {
            "baseline": {"state_entropy": 0.9890194745077442, "switching_rate": 0.1471},
            "perturbed": {"state_entropy": 0.9975767208489842, "switching_rate": 0.2032},
        },
    )
    _write_json(
        repo_root / "results" / "stage_2" / "stage_2_summary.json",
        {
            "initial_score": 5.243912073382831,
            "best_score": 0.9774,
            "best_metrics": {
                "within_network_stability": 0.29133552940286783,
                "cross_network_communication": 0.10138708629191759,
            },
            "best_metrics_mean": {
                "within_network_stability": 0.09622545907008154,
                "cross_network_communication": 0.04204893192358171,
            },
            "best_metrics_std": {
                "within_network_stability": 0.02390953677851308,
                "cross_network_communication": 0.02563396671958222,
            },
            "empirical_provenance": stage2_provenance
            or {
                "dataset_anchor": "OpenNeuro ds003059 placebo resting-state summary (15 session averages)",
                "subject_count": 15,
                "run_count": 60,
            },
            "empirical_validation_boundary": empirical_validation_boundary
            or {
                "held_out_validation_configured": False,
                "held_out_validation_completed": False,
                "held_out": False,
                "split_strategy": "none_all_available_targets_used_for_selection",
                "selection_subject_count": 15,
                "validation_subject_count": 0,
                "overlap_count": 0,
                "claim_guardrail": "No subject-disjoint held-out validation is configured.",
            },
        },
    )
    _write_json(
        repo_root / "results" / "stage_3" / "stage_3_summary.json",
        stage3_payload
        or {
            "best_mechanism": "less_hierarchical_constraint",
            "best_strength": 0.25,
            "best_score": 3481.5367151083433,
        },
    )
    _write_json(
        repo_root / "results" / "stage_4" / "stage_4_summary.json",
        stage4_payload
        or {
            "single_mechanisms": [
                {
                    "label": "less_hierarchical_constraint",
                    "score": 3481.5367151083433,
                }
            ],
            "pairwise_mechanisms": [
                {
                    "label": "less_hierarchical_constraint+more_stochasticity",
                    "score": 3498.3309152160546,
                }
            ],
        },
    )
    _write_json(
        repo_root / "results" / "training" / "condition_benchmark" / "comparison_summary.json",
        {"models": condition_models or [{"name": "temporal_cnn", "balanced_accuracy": 0.595}]},
    )
    _write_json(
        repo_root / "results" / "training" / "multitask_benchmark" / "comparison_summary.json",
        {
            "models": [
                {
                    "name": "hist_gradient_boosting_multitask",
                    "eigen_r2": 0.2616,
                }
            ]
        },
    )
    _write_yaml(
        repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml",
        {
            "target_deltas": empirical_target_deltas
            or {
                "within_network_stability": 0.06609328671299261,
                "cross_network_communication": 0.07407619939923198,
                "thalamic_coupling": 0.11991820431751381,
                "hierarchical_compression": 0.054149688768586765,
                "entropy_diversity": 0.0022526077494528915,
                "switching_rate": 0.012345679012345678,
                "metastability_proxy": 0.0,
                "effective_barrier_proxy": -0.1491923940892797,
            },
            "confidence": {
                "within_network_stability": "moderate",
                "cross_network_communication": "strong",
                "thalamic_coupling": "strong",
                "hierarchical_compression": "weak",
                "entropy_diversity": "weak",
                "switching_rate": "weak",
                "metastability_proxy": "moderate",
                "effective_barrier_proxy": "weak",
            },
        },
    )
    _write_yaml(
        repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml",
        {
            "target_deltas": literature_target_deltas
            or {
                "within_network_stability": -0.30,
                "cross_network_communication": 0.25,
                "thalamic_coupling": 0.20,
                "hierarchical_compression": 0.20,
                "entropy_diversity": 0.25,
                "switching_rate": 0.40,
                "metastability_proxy": 0.20,
                "effective_barrier_proxy": -0.25,
            },
            "confidence": {
                "within_network_stability": "strong",
                "cross_network_communication": "strong",
                "thalamic_coupling": "moderate_strong",
                "hierarchical_compression": "moderate",
                "entropy_diversity": "moderate",
                "switching_rate": "moderate",
                "metastability_proxy": "moderate",
                "effective_barrier_proxy": "weak",
            },
        },
    )


def test_build_publication_evidence_collects_stage_metrics(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(repo_root)

    evidence = build_publication_evidence(repo_root)

    assert evidence.stage2.best_score == 0.9774
    assert evidence.stage2.subject_count == 15
    assert evidence.stage3.best_mechanism == "less_hierarchical_constraint"
    assert evidence.stage4.best_pair_score > evidence.stage4.best_single_score
    assert evidence.sign_mismatches == ["within_network_stability"]
    assert "metastability_proxy" not in evidence.sign_mismatches
    assert evidence.stage2.validation_boundary.configured is False
    assert evidence.stage2.validation_boundary.completed is False


def test_build_publication_evidence_collects_optional_rocket_benchmark(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(repo_root)
    rocket_dir = repo_root / "results" / "training" / "rocket_condition_benchmark"
    rocket_dir.mkdir(parents=True)
    _write_json(
        rocket_dir / "comparison_summary.json",
        {
            "schema_version": "rocket_condition_benchmark.v1",
            "model": "rocket_random_convolution_features_logistic_regression",
            "cv_strategy": "approved CV5 subject-disjoint manifest",
            "primary_evaluation_unit": "subject_session_run_aggregated_windows",
            "primary_metric_source": "subject/session/run mean probability after subject-disjoint fold prediction",
            "window_random_reporting": False,
            "dataset": {"sample_count": 600, "subject_count": 15, "fold_count": 5},
            "rocket": {"n_kernels": 128, "feature_count": 256},
            "aggregate": {
                "accuracy_mean": 0.633,
                "accuracy_std": 0.145,
                "balanced_accuracy_mean": 0.633,
                "balanced_accuracy_std": 0.145,
                "roc_auc_mean": 0.744,
                "roc_auc_std": 0.147,
            },
            "claim_guardrail": "Internal subject-disjoint proxy classification diagnostic only.",
        },
    )

    evidence = build_publication_evidence(repo_root)

    assert evidence.rocket_benchmark is not None
    assert evidence.rocket_benchmark["cv_strategy"] == "approved CV5 subject-disjoint manifest"
    assert evidence.rocket_benchmark["primary_evaluation_unit"] == "subject_session_run_aggregated_windows"
    assert evidence.rocket_benchmark["balanced_accuracy_mean"] == 0.633
    assert evidence.rocket_benchmark["roc_auc_mean"] == 0.744


def test_build_publication_evidence_normalizes_dict_models_payload(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(
        repo_root,
        condition_models={"temporal_cnn": {"balanced_accuracy": 0.595}},
    )

    evidence = build_publication_evidence(repo_root)

    assert evidence.condition_models == [
        {
            "name": "temporal_cnn",
            "balanced_accuracy": 0.595,
        }
    ]


def test_publication_content_ranks_nested_aggregate_model_scores(tmp_path: Path) -> None:
    from lsd_thesis.publication_content import build_defense_outline_markdown, build_thesis_report_markdown
    from lsd_thesis.publication_figures import PublicationFigure

    repo_root = tmp_path / "repo"
    _write_publication_fixture(
        repo_root,
        condition_models=[
            {"name": "top_level_model", "balanced_accuracy": 0.51},
            {"name": "nested_model", "aggregate": {"balanced_accuracy_mean": 0.76}},
        ],
    )

    evidence = build_publication_evidence(repo_root)
    figures = {
        "stage1_metric_shift": PublicationFigure(
            figure_id="stage1_metric_shift",
            path=tmp_path / "stage1.png",
            caption="Stage 1.",
            limitations="Proxy only.",
        ),
        "stage2_fit_robustness": PublicationFigure(
            figure_id="stage2_fit_robustness",
            path=tmp_path / "stage2.png",
            caption="Stage 2.",
            limitations="Proxy only.",
        ),
    }
    report = build_thesis_report_markdown(evidence, figures)
    outline = build_defense_outline_markdown(evidence)

    assert "nested_model" in report
    assert "top_level_model" not in report
    assert "talking points" in outline.lower()


def test_build_publication_evidence_rejects_non_mapping_yaml_payload(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(repo_root)
    _write_yaml(
        repo_root / "configs" / "targets" / "empirical_lsd_signatures.yaml",
        ["not", "a", "mapping"],
    )

    with pytest.raises(ValueError, match="YAML mapping"):
        build_publication_evidence(repo_root)


def test_build_publication_evidence_rejects_unsupported_models_payload(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(repo_root)
    _write_json(
        repo_root / "results" / "training" / "condition_benchmark" / "comparison_summary.json",
        {"models": "unsupported"},
    )

    with pytest.raises(ValueError, match="models"):
        build_publication_evidence(repo_root)


def test_build_publication_evidence_rejects_missing_stage2_provenance_fields(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(
        repo_root,
        stage2_provenance={
            "dataset_anchor": "OpenNeuro ds003059 placebo resting-state summary (15 session averages)",
            "run_count": 60,
        },
    )

    with pytest.raises(ValueError, match="Stage 2 provenance"):
        build_publication_evidence(repo_root)


def test_build_publication_evidence_rejects_false_completed_holdout_claim(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(
        repo_root,
        empirical_validation_boundary={
            "held_out_validation_configured": False,
            "held_out_validation_completed": True,
            "held_out": True,
            "split_strategy": "none_all_available_targets_used_for_selection",
            "selection_subject_count": 15,
            "validation_subject_count": 0,
            "overlap_count": 0,
            "claim_guardrail": "invalid fixture",
        },
    )

    with pytest.raises(ValueError, match="held-out validation"):
        build_publication_evidence(repo_root)


def test_build_publication_evidence_rejects_candidate_completed_holdout_claim(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(
        repo_root,
        empirical_validation_boundary={
            "held_out_validation_configured": True,
            "held_out_validation_completed": True,
            "held_out": True,
            "split_id": "candidate_fixture",
            "split_strategy": "subject_disjoint",
            "approval_status": "candidate",
            "selection_subject_count": 12,
            "validation_subject_count": 3,
            "overlap_count": 0,
            "claim_guardrail": "invalid fixture",
        },
    )

    with pytest.raises(ValueError, match="approved split"):
        build_publication_evidence(repo_root)


def test_build_publication_evidence_prefers_completed_stage3_holdout_boundary(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(
        repo_root,
        empirical_validation_boundary={
            "held_out_validation_configured": True,
            "held_out_validation_completed": False,
            "held_out": False,
            "split_id": "approved_fixture",
            "split_strategy": "subject_disjoint",
            "approval_status": "approved",
            "selection_subject_count": 12,
            "validation_subject_count": 3,
            "overlap_count": 0,
            "claim_guardrail": "Approved split configured, not completed.",
        },
        stage3_payload={
            "best_mechanism": "less_hierarchical_constraint",
            "best_strength": 0.25,
            "best_score": 3481.5367151083433,
            "empirical_validation_boundary": {
                "held_out_validation_configured": True,
                "held_out_validation_completed": True,
                "held_out": True,
                "split_id": "approved_fixture",
                "split_strategy": "subject_disjoint",
                "approval_status": "approved",
                "selection_subject_count": 12,
                "validation_subject_count": 3,
                "overlap_count": 0,
                "claim_guardrail": "Subject-disjoint held-out validation has been completed and recorded.",
            },
        },
    )

    evidence = build_publication_evidence(repo_root)

    assert evidence.stage2.validation_boundary.completed is True
    assert evidence.stage2.validation_boundary.approval_status == "approved"


def test_build_publication_evidence_rejects_cv5_completed_without_internal_caveats(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(repo_root)
    cv5_dir = repo_root / "output" / "validation" / "cv5_subject_disjoint" / "results"
    cv5_dir.mkdir(parents=True)
    _write_json(
        cv5_dir / "cv5_aggregate_validation.json",
        {
            "approval_status": "approved",
            "validation_claim_scope": "preliminary_internal_subject_disjoint_cv5",
            "held_out_validation_completed": True,
            "all_folds_completed": True,
            "all_subjects_held_out_once": True,
            "limitations": ["Internal validation only"],
            "warnings": [],
        },
    )

    with pytest.raises(ValueError, match="missing required caveat"):
        build_publication_evidence(repo_root)


def test_build_publication_evidence_rejects_missing_target_deltas(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(repo_root)
    _write_yaml(
        repo_root / "results" / "stage_2" / "empirical_perturbation_targets.yaml",
        {"metadata": {"source_strategy": "actual_ds003059"}},
    )

    with pytest.raises(ValueError, match="target_deltas"):
        build_publication_evidence(repo_root)


def test_build_publication_evidence_reads_stage4_best_single_and_best_pair_schema(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_publication_fixture(
        repo_root,
        stage4_payload={
            "best_single": {
                "mechanism": "less_hierarchical_constraint",
                "score": 3481.5367151083433,
            },
            "best_pair": {
                "mechanism_pair": "less_hierarchical_constraint+more_stochasticity",
                "score": 3498.3309152160546,
            },
        },
    )

    evidence = build_publication_evidence(repo_root)

    assert evidence.stage4.best_single_mechanism == "less_hierarchical_constraint"
    assert evidence.stage4.best_single_score == 3481.5367151083433
    assert evidence.stage4.best_pair_name == "less_hierarchical_constraint+more_stochasticity"
    assert evidence.stage4.best_pair_score == 3498.3309152160546
