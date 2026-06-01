from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.web.status_payload import (
    build_empirical_validation_payload,
    build_model_selection_payload,
    build_provenance_payload,
    load_cv5_validation_payload,
)


def test_status_payload_helpers_expose_dashboard_model_and_validation_state(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    cv5_results_dir = repo_root / "output" / "validation" / "cv5_subject_disjoint" / "results"
    cv5_results_dir.mkdir(parents=True)
    (cv5_results_dir / "cv5_aggregate_validation.json").write_text(
        json.dumps(
            {
                "completed_folds": 5,
                "total_folds": 5,
                "held_out_validation_completed": True,
            }
        ),
        encoding="utf-8",
    )
    stage_summaries = {
        "stage_2": {
            "best_score": 0.9,
            "selected_iteration": 2,
            "fit_seed_plan": {
                "selection_mode": "multi_seed_mean",
                "validation_mode": "disjoint_seed_panel",
                "selection_seeds": [111, 112, 113],
                "validation_seeds": [1011, 1012],
            },
            "multi_seed_summary": {"score_mean": 0.95, "score_std": 0.05, "std_metrics": {"a": 0.1}},
            "empirical_validation_boundary": {
                "held_out_validation_configured": True,
                "held_out_validation_completed": False,
                "selection_subject_count": 2,
                "validation_subject_count": 1,
            },
            "empirical_provenance": {
                "dataset_anchor": "Empirical anchor",
                "subject_count": 2,
                "run_count": 4,
                "sessions": ["ses-LSD", "ses-PLCB"],
                "target_paths": {"sober": str(repo_root / "sober.yaml")},
            },
            "version_stamp": {"timestamp": "2026-04-13T00:00:00+00:00", "git": {"head_present": False}},
        }
    }

    provenance = build_provenance_payload(stage_summaries)
    model_selection = build_model_selection_payload(stage_summaries)
    empirical_validation = build_empirical_validation_payload(stage_summaries)
    cv5_validation = load_cv5_validation_payload(repo_root)

    assert provenance["dataset_anchor"] == "Empirical anchor"
    assert provenance["target_filenames"]["sober"] == "sober.yaml"
    assert model_selection["selection_seed_count"] == 3
    assert model_selection["validation_score_mean"] == 0.95
    assert empirical_validation["approval_status"] == "candidate"
    assert empirical_validation["selection_subject_count"] == 2
    assert cv5_validation is not None
    assert cv5_validation["source_path"] == "output/validation/cv5_subject_disjoint/results/cv5_aggregate_validation.json"
