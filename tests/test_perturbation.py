from pathlib import Path
from typing import Any

import numpy as np

from lsd_thesis.data.targets import load_perturbation_target_set
from lsd_thesis.fit import FitResult
from lsd_thesis.graph import load_graph_config
from lsd_thesis.perturbation import (
    PerturbationEvaluation,
    RobustPerturbationEvaluation,
    apply_mechanism,
    evaluate_perturbation_seed_panel,
    generate_stage_3_outputs,
    rank_perturbation_mechanisms,
    rank_perturbation_mechanisms_seed_panel,
    seed_noise_null_summary,
)
from lsd_thesis.simulator import load_regime_config

ROOT = Path(__file__).resolve().parents[1]


def test_apply_mechanism_changes_expected_parameter_direction() -> None:
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    cross_talk = apply_mechanism(baseline, "more_cross_talk", 0.2)
    barrier = apply_mechanism(baseline, "lower_switching_barrier", 0.2)

    assert (
        cross_talk.global_parameters.cross_group_scale
        > baseline.global_parameters.cross_group_scale
    )
    assert barrier.module_defaults.barrier < baseline.module_defaults.barrier


def test_rank_perturbation_mechanisms_returns_all_core_mechanisms() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    target_set = load_perturbation_target_set(
        ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    )

    ranking = rank_perturbation_mechanisms(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        strengths=(0.1,),
    )

    mechanisms = {item.mechanism for item in ranking}
    assert mechanisms == {
        "more_cross_talk",
        "less_hierarchical_constraint",
        "more_stochasticity",
        "lower_switching_barrier",
    }
    assert ranking[0].score >= 0.0


def test_seed_panel_ranking_reports_uncertainty_and_null_summary() -> None:
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    target_set = load_perturbation_target_set(
        ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml"
    )
    seeds = (3, 4)

    evaluation = evaluate_perturbation_seed_panel(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        mechanism="more_cross_talk",
        strength=0.1,
        seeds=seeds,
    )
    ranking = rank_perturbation_mechanisms_seed_panel(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        strengths=(0.1,),
        seeds=seeds,
    )
    null_summary = seed_noise_null_summary(
        graph=graph,
        sober_regime=baseline,
        target_set=target_set,
        seeds=seeds,
    )

    assert evaluation.seed_count == 2
    assert evaluation.score_mean >= 0.0
    assert evaluation.score_std >= 0.0
    assert 0.0 <= evaluation.sign_agreement_fraction <= 1.0
    assert len(ranking) == 4
    assert null_summary["seed_count"] == 2
    assert null_summary["score_mean"] >= 0.0


def test_stage_3_summary_records_configured_subject_split_without_completed_holdout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    split_path = tmp_path / "subject_split.json"
    split_path.write_text(
        """{
          "schema_version": 1,
          "split_id": "fixture_stage3_split",
          "strategy": "subject_disjoint",
          "selection_subjects": ["sub-001", "sub-002"],
          "validation_subjects": ["sub-003"],
          "split_seed": 123
        }""",
        encoding="utf-8",
    )
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    monkeypatch.setattr(
        "lsd_thesis.perturbation.fit_sober_regime",
        lambda **kwargs: FitResult(
            initial_score=1.0,
            best_score=0.5,
            best_regime=baseline,
            best_metrics={},
            best_fc_matrix=np.eye(len(graph.modules)),
            history=[],
        ),
    )

    def fake_ranking(**kwargs: Any) -> list[PerturbationEvaluation]:
        target_set = kwargs["target_set"]
        return [
            PerturbationEvaluation(
                mechanism="more_cross_talk",
                strength=0.1,
                score=1.0,
                delta_metrics={name: 0.0 for name in target_set.target_deltas},
                perturbed_metrics={name: 0.0 for name in target_set.target_deltas},
            )
        ]

    def fake_robust_ranking(**kwargs: Any) -> list[RobustPerturbationEvaluation]:
        target_set = kwargs["target_set"]
        return [
            RobustPerturbationEvaluation(
                mechanism="more_cross_talk",
                strength=0.1,
                seed_count=2,
                score_mean=1.0,
                score_std=0.0,
                delta_metrics_mean={name: 0.0 for name in target_set.target_deltas},
                delta_metrics_std={name: 0.0 for name in target_set.target_deltas},
                perturbed_metrics_mean={name: 0.0 for name in target_set.target_deltas},
                sign_agreement_fraction=0.0,
            )
        ]

    monkeypatch.setattr("lsd_thesis.perturbation.rank_perturbation_mechanisms", fake_ranking)
    monkeypatch.setattr("lsd_thesis.perturbation.rank_perturbation_mechanisms_seed_panel", fake_robust_ranking)
    monkeypatch.setattr(
        "lsd_thesis.perturbation.seed_noise_null_summary",
        lambda **kwargs: {"seed_count": 2, "score_mean": 2.0, "score_std": 0.1},
    )
    monkeypatch.setattr("lsd_thesis.perturbation._save_figure", lambda figure, path: path.write_text("<html></html>", encoding="utf-8"))

    summary = generate_stage_3_outputs(
        graph_path=ROOT / "configs" / "graphs" / "macro_modules.yaml",
        baseline_path=ROOT / "configs" / "regimes" / "baseline.yaml",
        sober_target_path=ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
        perturbation_target_path=ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml",
        output_dir=tmp_path / "stage_3",
        report_path=tmp_path / "stage_3.md",
        fit_iterations=1,
        strengths=(0.1,),
        seed=11,
        seed_panel=(101, 102),
        subject_split_path=split_path,
    )

    boundary = summary["empirical_validation_boundary"]
    assert boundary["held_out_validation_configured"] is True
    assert boundary["held_out_validation_completed"] is False
    assert boundary["held_out"] is False
    assert boundary["split_id"] == "fixture_stage3_split"
    assert boundary["approval_status"] == "candidate"
    assert boundary["boundary_type"] == "subject_disjoint_candidate_configured_not_completed"
    assert boundary["selection_subject_count"] == 2
    assert boundary["validation_subject_count"] == 1


def test_stage_3_approved_split_evaluates_heldout_targets_and_marks_completed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    split_path = tmp_path / "approved_subject_split.json"
    split_path.write_text(
        """{
          "schema_version": 1,
          "split_id": "fixture_stage3_approved_split",
          "strategy": "subject_disjoint",
          "selection_subjects": ["sub-001", "sub-002"],
          "validation_subjects": ["sub-003"],
          "split_seed": 123,
          "approval_status": "approved",
          "approved_by": "pytest-reviewer",
          "approved_at": "2026-05-10T00:00:00Z"
        }""",
        encoding="utf-8",
    )
    graph = load_graph_config(ROOT / "configs" / "graphs" / "macro_modules.yaml")
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")

    monkeypatch.setattr(
        "lsd_thesis.perturbation.fit_sober_regime",
        lambda **kwargs: FitResult(
            initial_score=1.0,
            best_score=0.5,
            best_regime=baseline,
            best_metrics={},
            best_fc_matrix=np.eye(len(graph.modules)),
            history=[],
        ),
    )

    def fake_ranking(**kwargs: Any) -> list[PerturbationEvaluation]:
        target_set = kwargs["target_set"]
        return [
            PerturbationEvaluation(
                mechanism="more_cross_talk",
                strength=0.1,
                score=1.0,
                delta_metrics={name: 0.0 for name in target_set.target_deltas},
                perturbed_metrics={name: 0.0 for name in target_set.target_deltas},
            )
        ]

    def fake_robust_ranking(**kwargs: Any) -> list[RobustPerturbationEvaluation]:
        target_set = kwargs["target_set"]
        return [
            RobustPerturbationEvaluation(
                mechanism="more_cross_talk",
                strength=0.1,
                seed_count=2,
                score_mean=1.0,
                score_std=0.0,
                delta_metrics_mean={name: 0.0 for name in target_set.target_deltas},
                delta_metrics_std={name: 0.0 for name in target_set.target_deltas},
                perturbed_metrics_mean={name: 0.0 for name in target_set.target_deltas},
                sign_agreement_fraction=0.0,
            )
        ]

    monkeypatch.setattr("lsd_thesis.perturbation.rank_perturbation_mechanisms", fake_ranking)
    monkeypatch.setattr("lsd_thesis.perturbation.rank_perturbation_mechanisms_seed_panel", fake_robust_ranking)
    monkeypatch.setattr(
        "lsd_thesis.perturbation.seed_noise_null_summary",
        lambda **kwargs: {"seed_count": 2, "score_mean": 2.0, "score_std": 0.1},
    )
    monkeypatch.setattr(
        "lsd_thesis.perturbation.evaluate_perturbation_seed_panel",
        lambda **kwargs: RobustPerturbationEvaluation(
            mechanism="more_cross_talk",
            strength=0.1,
            seed_count=2,
            score_mean=0.75,
            score_std=0.05,
            delta_metrics_mean={"within_network_stability": 0.01},
            delta_metrics_std={"within_network_stability": 0.001},
            perturbed_metrics_mean={"within_network_stability": 0.2},
            sign_agreement_fraction=1.0,
        ),
    )
    monkeypatch.setattr("lsd_thesis.perturbation._save_figure", lambda figure, path: path.write_text("<html></html>", encoding="utf-8"))

    summary = generate_stage_3_outputs(
        graph_path=ROOT / "configs" / "graphs" / "macro_modules.yaml",
        baseline_path=ROOT / "configs" / "regimes" / "baseline.yaml",
        sober_target_path=ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
        perturbation_target_path=ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml",
        heldout_sober_target_path=ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
        heldout_perturbation_target_path=ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml",
        output_dir=tmp_path / "stage_3",
        report_path=tmp_path / "stage_3.md",
        fit_iterations=1,
        strengths=(0.1,),
        seed=11,
        seed_panel=(101, 102),
        subject_split_path=split_path,
    )

    boundary = summary["empirical_validation_boundary"]
    assert boundary["approval_status"] == "approved"
    assert boundary["held_out_validation_completed"] is True
    assert boundary["boundary_type"] == "subject_disjoint_approved_completed"
    assert summary["heldout_validation_evaluation"]["status"] == "completed"
    assert summary["heldout_validation_evaluation"]["score_mean"] == 0.75


def test_stage_3_approved_split_requires_heldout_targets(tmp_path: Path, monkeypatch) -> None:
    split_path = tmp_path / "approved_subject_split.json"
    split_path.write_text(
        """{
          "schema_version": 1,
          "split_id": "fixture_stage3_approved_split",
          "strategy": "subject_disjoint",
          "selection_subjects": ["sub-001", "sub-002"],
          "validation_subjects": ["sub-003"],
          "approval_status": "approved",
          "approved_by": "pytest-reviewer",
          "approved_at": "2026-05-10T00:00:00Z"
        }""",
        encoding="utf-8",
    )
    baseline = load_regime_config(ROOT / "configs" / "regimes" / "baseline.yaml")
    monkeypatch.setattr(
        "lsd_thesis.perturbation.fit_sober_regime",
        lambda **kwargs: FitResult(
            initial_score=1.0,
            best_score=0.5,
            best_regime=baseline,
            best_metrics={},
            best_fc_matrix=np.eye(2),
            history=[],
        ),
    )
    def fake_required_ranking(**kwargs: Any) -> list[PerturbationEvaluation]:
        target_set = kwargs["target_set"]
        return [
            PerturbationEvaluation(
                mechanism="more_cross_talk",
                strength=0.1,
                score=1.0,
                delta_metrics={name: 0.0 for name in target_set.target_deltas},
                perturbed_metrics={name: 0.0 for name in target_set.target_deltas},
            )
        ]

    def fake_required_robust_ranking(**kwargs: Any) -> list[RobustPerturbationEvaluation]:
        target_set = kwargs["target_set"]
        return [
            RobustPerturbationEvaluation(
                mechanism="more_cross_talk",
                strength=0.1,
                seed_count=2,
                score_mean=1.0,
                score_std=0.0,
                delta_metrics_mean={name: 0.0 for name in target_set.target_deltas},
                delta_metrics_std={name: 0.0 for name in target_set.target_deltas},
                perturbed_metrics_mean={name: 0.0 for name in target_set.target_deltas},
                sign_agreement_fraction=0.0,
            )
        ]

    monkeypatch.setattr("lsd_thesis.perturbation.rank_perturbation_mechanisms", fake_required_ranking)
    monkeypatch.setattr(
        "lsd_thesis.perturbation.rank_perturbation_mechanisms_seed_panel",
        fake_required_robust_ranking,
    )
    monkeypatch.setattr(
        "lsd_thesis.perturbation.seed_noise_null_summary",
        lambda **kwargs: {"seed_count": 2, "score_mean": 2.0, "score_std": 0.1},
    )
    monkeypatch.setattr("lsd_thesis.perturbation._save_figure", lambda figure, path: path.write_text("<html></html>", encoding="utf-8"))

    try:
        generate_stage_3_outputs(
            graph_path=ROOT / "configs" / "graphs" / "macro_modules.yaml",
            baseline_path=ROOT / "configs" / "regimes" / "baseline.yaml",
            sober_target_path=ROOT / "configs" / "targets" / "sober_summary_targets.yaml",
            perturbation_target_path=ROOT / "configs" / "targets" / "empirical_lsd_signatures.yaml",
            output_dir=tmp_path / "stage_3",
            report_path=tmp_path / "stage_3.md",
            fit_iterations=1,
            strengths=(0.1,),
            seed=11,
            seed_panel=(101, 102),
            subject_split_path=split_path,
        )
    except ValueError as exc:
        assert "held-out sober and perturbation target paths" in str(exc)
    else:
        raise AssertionError("Expected approved Stage 3 split to require held-out target paths.")
