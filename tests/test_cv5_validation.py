from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from lsd_thesis.cv5_validation import (
    refresh_cv5_aggregate_from_existing_outputs,
    run_cv5_validation,
)
from lsd_thesis.subject_split import (
    SubjectSplit,
    create_cv5_subject_split_package,
    load_subject_split_file,
    subject_split_json_payload,
    validate_cv5_subject_split_manifest,
)


def _write_approved_cv5_package(repo_root: Path) -> Path:
    split_dir = repo_root / "splits"
    fold_paths = [f"splits/subject_split_fold_{index:02d}_approved.json" for index in range(1, 3)]
    folds, manifest = create_cv5_subject_split_package(
        ["sub-001", "sub-002", "sub-003", "sub-004"],
        split_set_id="cv5_fixture_candidate",
        seed=123,
        number_of_folds=2,
        fold_file_paths=fold_paths,
    )
    split_dir.mkdir(parents=True)
    for index, fold in enumerate(folds, start=1):
        payload = subject_split_json_payload(fold)
        payload.update(
            {
                "split_id": f"cv5_fixture_approved_fold_{index:02d}",
                "approval_status": "approved",
                "approved_by": "pytest",
                "approved_at": "2026-05-10T00:00:00Z",
                "validation_claim_scope": "preliminary_internal_subject_disjoint_cv5",
            }
        )
        approved = SubjectSplit.model_validate(payload)
        (repo_root / fold_paths[index - 1]).write_text(
            json.dumps(subject_split_json_payload(approved)),
            encoding="utf-8",
        )
    manifest.update(
        {
            "split_set_id": "cv5_fixture_approved",
            "approval_status": "approved",
            "approved_by": "pytest",
            "approved_at": "2026-05-10T00:00:00Z",
            "validation_claim_scope": "preliminary_internal_subject_disjoint_cv5",
            "fold_file_paths": fold_paths,
            "held_out_validation_completed": False,
            "limitations": ["Internal validation only; not external validation"],
        }
    )
    manifest_path = split_dir / "subject_split_cv5_manifest_approved.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    validate_cv5_subject_split_manifest(manifest_path, repo_root=repo_root)
    return manifest_path


def _fake_stage2(**kwargs: Any) -> dict[str, Any]:
    output_dir = Path(kwargs["output_dir"])
    split = load_subject_split_file(kwargs["subject_split_path"])
    output_dir.mkdir(parents=True, exist_ok=True)
    heldout_dir = output_dir / "heldout_validation"
    heldout_dir.mkdir(parents=True, exist_ok=True)
    sober_path = output_dir / "empirical_sober_targets.yaml"
    perturbation_path = output_dir / "empirical_perturbation_targets.yaml"
    heldout_sober_path = heldout_dir / "empirical_sober_targets.yaml"
    heldout_perturbation_path = heldout_dir / "empirical_perturbation_targets.yaml"
    for path in (sober_path, perturbation_path, heldout_sober_path, heldout_perturbation_path):
        path.write_text("fixture: true\n", encoding="utf-8")
    summary = {
        "empirical_subjects": list(split.selection_subjects),
        "empirical_validation_boundary": {
            "approval_status": "approved",
            "selection_subject_count": len(split.selection_subjects),
            "validation_subject_count": len(split.validation_subjects),
            "overlap_count": 0,
        },
        "heldout_validation_target_paths": {
            "sober": str(heldout_sober_path),
            "perturbation": str(heldout_perturbation_path),
            "subjects": list(split.validation_subjects),
        },
    }
    (output_dir / "stage_2_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return summary


def _fake_stage3(**kwargs: Any) -> dict[str, Any]:
    output_dir = Path(kwargs["output_dir"])
    split = load_subject_split_file(kwargs["subject_split_path"])
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "empirical_validation_boundary": {
            "approval_status": "approved",
            "held_out_validation_completed": True,
            "selection_subject_count": len(split.selection_subjects),
            "validation_subject_count": len(split.validation_subjects),
            "overlap_count": 0,
        },
        "heldout_validation_evaluation": {
            "status": "completed",
            "selected_mechanism": "more_cross_talk",
            "selected_strength": 0.1,
            "score_mean": float(len(split.validation_subjects)),
            "score_std": 0.01,
            "sign_agreement_fraction": 0.5,
            "delta_metrics_mean": {"entropy_diversity": 0.1},
            "delta_metrics_std": {"entropy_diversity": 0.01},
        },
    }
    (output_dir / "stage_3_summary.json").write_text(json.dumps(summary), encoding="utf-8")
    return summary


def test_run_cv5_validation_writes_fold_isolated_outputs_and_complete_aggregate(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_approved_cv5_package(tmp_path)
    monkeypatch.setattr("lsd_thesis.cv5_validation.generate_stage_2_outputs", _fake_stage2)
    monkeypatch.setattr("lsd_thesis.cv5_validation.generate_stage_3_outputs", _fake_stage3)
    monkeypatch.setattr("lsd_thesis.cv5_validation._write_empirical_cache_from_existing_stage2", lambda **kwargs: None)

    aggregate = run_cv5_validation(
        manifest_path=manifest_path,
        output_dir=tmp_path / "results",
        repo_root=tmp_path,
        fit_iterations=1,
        seed=11,
    )

    assert aggregate["held_out_validation_completed"] is True
    assert aggregate["status"] == "complete"
    assert aggregate["completed_folds"] == 2
    assert aggregate["all_folds_completed"] is True
    assert aggregate["all_subjects_held_out_once"] is True
    assert aggregate["run_parameters"]["fit_iterations"] == 1
    assert aggregate["run_parameters"]["seed"] == 11
    assert aggregate["run_parameters"]["run_command"].startswith(
        "uv run python scripts/run_cv5_validation.py --manifest"
    )
    assert aggregate["provenance"]["python_version"]
    assert (tmp_path / "results" / "fold_01" / "stage2" / "stage_2_summary.json").exists()
    assert (tmp_path / "results" / "fold_02" / "stage3" / "stage_3_summary.json").exists()
    assert (tmp_path / "results" / "cv5_aggregate_validation.json").exists()


def test_refresh_cv5_aggregate_from_existing_outputs_does_not_rerun_folds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_path = _write_approved_cv5_package(tmp_path)
    monkeypatch.setattr("lsd_thesis.cv5_validation.generate_stage_2_outputs", _fake_stage2)
    monkeypatch.setattr("lsd_thesis.cv5_validation.generate_stage_3_outputs", _fake_stage3)
    monkeypatch.setattr("lsd_thesis.cv5_validation._write_empirical_cache_from_existing_stage2", lambda **kwargs: None)
    run_cv5_validation(
        manifest_path=manifest_path,
        output_dir=tmp_path / "results",
        repo_root=tmp_path,
        fit_iterations=1,
        seed=11,
    )

    def fail_if_called(**kwargs: Any) -> dict[str, Any]:
        raise AssertionError("Stage functions must not run during aggregate-only refresh")

    monkeypatch.setattr("lsd_thesis.cv5_validation.generate_stage_2_outputs", fail_if_called)
    monkeypatch.setattr("lsd_thesis.cv5_validation.generate_stage_3_outputs", fail_if_called)

    aggregate = refresh_cv5_aggregate_from_existing_outputs(
        manifest_path=manifest_path,
        output_dir=tmp_path / "results",
        repo_root=tmp_path,
        fit_iterations=1,
        seed=11,
    )

    assert aggregate["held_out_validation_completed"] is True
    assert aggregate["run_parameters"]["aggregate_path"] == "results/cv5_aggregate_validation.json"


def test_run_cv5_validation_refuses_existing_fold_outputs(tmp_path: Path) -> None:
    manifest_path = _write_approved_cv5_package(tmp_path)
    existing = tmp_path / "results" / "fold_01" / "stage2"
    existing.mkdir(parents=True)
    (existing / "existing.json").write_text("{}", encoding="utf-8")

    with pytest.raises(FileExistsError, match="Refusing to run CV5 validation"):
        run_cv5_validation(
            manifest_path=manifest_path,
            output_dir=tmp_path / "results",
            repo_root=tmp_path,
            fit_iterations=1,
            seed=11,
        )
