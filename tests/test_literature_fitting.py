import csv
import json
from pathlib import Path
from uuid import uuid4

import numpy as np

from lsd_thesis.fitting_literature import (
    PerturbationCandidate,
    rank_ablation_candidates,
    run_stage_5_literature_fit,
    summarize_seed_metric_deltas,
)
from lsd_thesis.objectives import literature_weighted_lsd_objective


def _test_root() -> Path:
    root = Path("codex_logs") / "literature_fitting_tests" / uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_literature_objective_prefers_matching_model_delta() -> None:
    empirical = {"unimodal_transmodal_fc": 0.25, "transition_entropy": 0.10}

    matched = literature_weighted_lsd_objective(
        empirical_delta=empirical,
        model_delta={"unimodal_transmodal_fc": 0.25, "transition_entropy": 0.10},
    )
    mismatched = literature_weighted_lsd_objective(
        empirical_delta=empirical,
        model_delta={"unimodal_transmodal_fc": -0.25, "transition_entropy": 0.00},
    )

    assert matched["loss"] < mismatched["loss"]
    assert matched["metric_count"] == 2


def test_literature_objective_penalizes_sign_mismatch_and_overshoot() -> None:
    empirical = {"visual_global_connectivity": 0.20}

    sign_mismatch = literature_weighted_lsd_objective(
        empirical_delta=empirical,
        model_delta={"visual_global_connectivity": -0.20},
    )
    overshoot = literature_weighted_lsd_objective(
        empirical_delta=empirical,
        model_delta={"visual_global_connectivity": 0.55},
    )
    close = literature_weighted_lsd_objective(
        empirical_delta=empirical,
        model_delta={"visual_global_connectivity": 0.18},
    )

    assert sign_mismatch["sign_mismatch_penalty"] > 0.0
    assert overshoot["overshoot_penalty"] > 0.0
    assert close["loss"] < sign_mismatch["loss"]
    assert close["loss"] < overshoot["loss"]


def test_literature_objective_includes_seed_variance_penalty() -> None:
    empirical = {"transition_entropy": 0.10}

    stable = literature_weighted_lsd_objective(
        empirical_delta=empirical,
        seed_metric_deltas=[
            {"transition_entropy": 0.09},
            {"transition_entropy": 0.10},
            {"transition_entropy": 0.11},
        ],
    )
    unstable = literature_weighted_lsd_objective(
        empirical_delta=empirical,
        seed_metric_deltas=[
            {"transition_entropy": -0.20},
            {"transition_entropy": 0.10},
            {"transition_entropy": 0.40},
        ],
    )

    assert stable["seed_variance_penalty"] < unstable["seed_variance_penalty"]


def test_summarize_seed_metric_deltas_schema_is_stable() -> None:
    summary = summarize_seed_metric_deltas(
        [
            {"seed": 1, "metrics": {"a": 1.0, "b": 2.0}},
            {"seed": 2, "metrics": {"a": 3.0, "b": 4.0}},
        ]
    )

    assert summary == {
        "a": {"mean": 2.0, "std": float(np.std([1.0, 3.0], ddof=1)), "n": 2},
        "b": {"mean": 3.0, "std": float(np.std([2.0, 4.0], ddof=1)), "n": 2},
    }


def test_ablation_leaderboard_ranks_known_synthetic_winner() -> None:
    empirical = {"unimodal_transmodal_fc": 0.20, "transition_entropy": 0.10}
    leaderboard = rank_ablation_candidates(
        empirical_delta=empirical,
        candidate_deltas={
            "winner": {"unimodal_transmodal_fc": 0.20, "transition_entropy": 0.10},
            "wrong_sign": {"unimodal_transmodal_fc": -0.20, "transition_entropy": 0.10},
            "overshoot": {"unimodal_transmodal_fc": 0.70, "transition_entropy": 0.10},
        },
    )

    assert leaderboard[0]["label"] == "winner"
    assert leaderboard[0]["loss"] < leaderboard[-1]["loss"]


def test_stage_5_smoke_writes_required_artifacts() -> None:
    root = _test_root()
    target_summary_path = root / "target_reliability_summary.json"
    target_summary_path.write_text(
        json.dumps(
            {
                "metrics": {
                    "unimodal_transmodal_fc": {
                        "delta_mean": 0.01,
                        "delta_std": 0.02,
                        "ci_low": -0.01,
                        "ci_high": 0.03,
                    },
                    "transition_entropy": {
                        "delta_mean": 0.0,
                        "delta_std": 0.01,
                        "ci_low": -0.01,
                        "ci_high": 0.01,
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    candidates = (
        PerturbationCandidate("none", {}),
        PerturbationCandidate("gain_only", {"receptor_gain_alpha": 0.05}),
    )

    summary = run_stage_5_literature_fit(
        target_summary_path=target_summary_path,
        output_dir=root / "stage_5",
        report_path=root / "stage_5.md",
        seeds=(1,),
        candidates=candidates,
        model_config_overrides={"n_steps": 60, "burn_in": 10, "emit_bold": False, "noise_sigma": 0.0},
        n_bootstrap=16,
    )

    assert summary["candidate_count"] == 2
    assert (root / "stage_5" / "literature_weighted_fit_summary.json").exists()
    assert (root / "stage_5" / "placebo_fit_summary.json").exists()
    assert (root / "stage_5" / "lsd_perturbation_fit_summary.json").exists()
    assert (root / "stage_5" / "per_seed_metrics.csv").exists()
    assert (root / "stage_5" / "sign_match_table.csv").exists()
    assert (root / "stage_5" / "overshoot_table.csv").exists()
    assert (root / "stage_5" / "ablation_leaderboard.csv").exists()
    assert (root / "stage_5.md").exists()
    with (root / "stage_5" / "ablation_leaderboard.csv").open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert {row["label"] for row in rows} == {"none", "gain_only"}
