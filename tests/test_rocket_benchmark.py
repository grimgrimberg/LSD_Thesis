from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from lsd_thesis.rocket_benchmark import evaluate_rocket_condition_model, write_rocket_outputs
from lsd_thesis.subject_split import SubjectSplit, create_cv5_subject_split_package, subject_split_json_payload


def _synthetic_dataset(subjects: tuple[str, ...] = ("sub-001", "sub-002", "sub-003", "sub-004")) -> dict[str, np.ndarray]:
    timeline = np.linspace(0.0, 2.0 * np.pi, 32, endpoint=False)
    base_plcb = np.stack([np.sin(timeline + index * 0.1) for index in range(3)], axis=1)
    base_lsd = np.stack([np.cos(timeline + index * 0.2) + 1.25 for index in range(3)], axis=1)
    windows = []
    labels = []
    subject_rows = []
    sessions = []
    runs = []
    for subject_index, subject in enumerate(subjects):
        shift = subject_index * 0.03
        for session, label, base in (("ses-PLCB", 0, base_plcb), ("ses-LSD", 1, base_lsd)):
            for run in ("run-01", "run-03"):
                for replicate in range(2):
                    windows.append(base + shift + replicate * 0.01)
                    labels.append(label)
                    subject_rows.append(subject)
                    sessions.append(session)
                    runs.append(run)
    return {
        "windows": np.asarray(windows, dtype=float),
        "condition": np.asarray(labels, dtype=np.int8),
        "subject": np.asarray(subject_rows, dtype="U32"),
        "session": np.asarray(sessions, dtype="U16"),
        "run": np.asarray(runs, dtype="U16"),
    }


def test_rocket_transform_returns_two_features_per_kernel() -> None:
    dataset = _synthetic_dataset(("sub-001", "sub-002"))
    summary = evaluate_rocket_condition_model(dataset, n_kernels=6, random_state=123)

    assert summary["rocket"]["feature_count"] == 12
    assert summary["rocket"]["features_per_kernel"] == ["max", "proportion_positive_values"]
    assert summary["window_random_reporting"] is False


def test_evaluate_rocket_condition_model_uses_subject_held_out_aggregation() -> None:
    dataset = _synthetic_dataset()

    summary = evaluate_rocket_condition_model(dataset, n_kernels=24, random_state=123)

    assert summary["cv_strategy"] == "LeaveOneGroupOut(subject)"
    assert summary["primary_evaluation_unit"] == "subject_session_run_aggregated_windows"
    assert summary["primary_metric_source"].startswith("subject/session/run mean probability")
    assert summary["dataset"]["subject_count"] == 4
    assert len(summary["folds"]) == 4
    assert len(summary["subject_session_run_predictions"]) == 16
    assert len(summary["window_predictions_secondary"]) == 32
    assert all(row["window_count"] == 2 for row in summary["subject_session_run_predictions"])
    assert summary["aggregate"]["balanced_accuracy_mean"] >= 0.99
    assert "brier_score_mean" in summary["aggregate"]
    assert summary["calibration"]["brier_score"] <= 1.0
    assert summary["permutation_null"]["status"] == "not_run"


def test_evaluate_rocket_condition_model_can_run_posthoc_permutation_null() -> None:
    dataset = _synthetic_dataset()

    summary = evaluate_rocket_condition_model(dataset, n_kernels=12, random_state=123, n_permutations=5)

    assert summary["permutation_null"]["status"] == "completed"
    assert summary["permutation_null"]["n_permutations"] == 5
    assert summary["permutation_null"]["null_type"] == "posthoc_prediction_label_permutation_not_refit"
    assert 0.0 <= summary["permutation_null"]["balanced_accuracy_empirical_p_value"] <= 1.0


def _write_approved_cv5_manifest(repo_root: Path, subjects: tuple[str, ...]) -> Path:
    split_dir = repo_root / "splits"
    split_dir.mkdir(parents=True)
    fold_paths = [f"splits/subject_split_fold_{index:02d}_approved.json" for index in range(1, 3)]
    folds, manifest = create_cv5_subject_split_package(
        subjects,
        split_set_id="rocket_cv5_fixture_candidate",
        number_of_folds=2,
        fold_file_paths=fold_paths,
    )
    approved_paths = []
    for index, fold in enumerate(folds, start=1):
        payload = subject_split_json_payload(fold)
        payload.update(
            {
                "split_id": f"rocket_cv5_fixture_approved_fold_{index:02d}",
                "approval_status": "approved",
                "approved_by": "pytest",
                "approved_at": "2026-05-26T00:00:00Z",
                "limitations": ["Internal validation only"],
            }
        )
        approved = SubjectSplit.model_validate(payload)
        fold_path = repo_root / fold_paths[index - 1]
        fold_path.write_text(json.dumps(subject_split_json_payload(approved), indent=2), encoding="utf-8")
        approved_paths.append(fold_paths[index - 1])
    manifest.update(
        {
            "split_set_id": "rocket_cv5_fixture_approved",
            "approval_status": "approved",
            "approved_by": "pytest",
            "approved_at": "2026-05-26T00:00:00Z",
            "fold_file_paths": approved_paths,
            "validation_claim_scope": "preliminary_internal_subject_disjoint_cv5",
            "limitations": ["Internal validation only"],
        }
    )
    manifest_path = split_dir / "subject_split_cv5_manifest_approved.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest_path


def test_evaluate_rocket_condition_model_can_use_approved_cv5_manifest(tmp_path: Path) -> None:
    subjects = ("sub-001", "sub-002", "sub-003", "sub-004")
    manifest_path = _write_approved_cv5_manifest(tmp_path, subjects)
    dataset = _synthetic_dataset(subjects)

    summary = evaluate_rocket_condition_model(
        dataset,
        n_kernels=12,
        random_state=321,
        cv5_manifest_path=manifest_path,
        repo_root=tmp_path,
    )

    assert summary["cv_strategy"] == "approved CV5 subject-disjoint manifest"
    assert summary["split_summary"]["validation_coverage_summary"]["every_subject_held_out_exactly_once"] is True
    assert len(summary["folds"]) == 2
    assert {fold["held_out_subject_count"] for fold in summary["folds"]} == {2}
    assert summary["aggregate"]["balanced_accuracy_mean"] >= 0.99


def test_write_rocket_outputs_records_primary_and_secondary_predictions(tmp_path: Path) -> None:
    dataset = _synthetic_dataset(("sub-001", "sub-002"))
    summary = evaluate_rocket_condition_model(dataset, n_kernels=8, random_state=99)

    write_rocket_outputs(summary, tmp_path)

    assert (tmp_path / "comparison_summary.json").exists()
    assert (tmp_path / "subject_session_run_predictions.csv").exists()
    assert (tmp_path / "window_predictions_secondary.csv").exists()
    report = (tmp_path / "benchmark_report.md").read_text(encoding="utf-8")
    assert "No random window-level train/test split is used." in report
    assert "Calibration and Null Gates" in report
    payload = json.loads((tmp_path / "comparison_summary.json").read_text(encoding="utf-8"))
    assert payload["primary_evaluation_unit"] == "subject_session_run_aggregated_windows"
    assert "calibration" in payload
