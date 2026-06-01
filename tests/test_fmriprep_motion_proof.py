from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from lsd_thesis.fmriprep_motion_proof import build_fmriprep_motion_proof_plan, write_fmriprep_motion_proof_plan


def _write_dataset_description(root: Path, dataset_type: str) -> None:
    dataset_root = root / "data" / "ds003059"
    dataset_root.mkdir(parents=True, exist_ok=True)
    (dataset_root / "dataset_description.json").write_text(
        json.dumps({"Name": "fixture", "DatasetType": dataset_type, "BIDSVersion": "1.4.0"}),
        encoding="utf-8",
    )


def test_fmriprep_motion_plan_blocks_derivative_snapshot(tmp_path: Path) -> None:
    _write_dataset_description(tmp_path, "derivative")
    bold_dir = tmp_path / "data" / "ds003059" / "sub-001" / "ses-LSD" / "func"
    anat_dir = tmp_path / "data" / "ds003059" / "sub-001" / "anat"
    bold_dir.mkdir(parents=True)
    anat_dir.mkdir(parents=True)
    (bold_dir / "sub-001_ses-LSD_task-rest_run-01_bold.nii.gz").write_bytes(b"not-a-real-nifti")
    (anat_dir / "._sub-001_T1w.nii.gz").write_bytes(b"appledouble-placeholder")

    payload = build_fmriprep_motion_proof_plan(tmp_path, runtime_availability={"docker": True})

    assert payload["analysis_status"] == "blocked_derivative_snapshot_not_valid_raw_fmriprep_input"
    assert payload["fmriprep_motion_proof_ready"] is False
    assert payload["fmriprep_preflight_ready"] is False
    assert payload["local_nifti_state"]["local_bold_run_count"] == 1
    assert payload["local_nifti_state"]["local_t1w_count"] == 0
    assert "DatasetType=derivative" in payload["blocker"]


def test_fmriprep_motion_plan_detects_existing_structured_confounds(tmp_path: Path) -> None:
    _write_dataset_description(tmp_path, "raw")
    confound_dir = tmp_path / "data" / "ds003059" / "derivatives" / "fmriprep" / "sub-001" / "ses-LSD" / "func"
    confound_dir.mkdir(parents=True)
    pd.DataFrame({"framewise_displacement": [0.0, 0.1], "std_dvars": [1.0, 1.2]}).to_csv(
        confound_dir / "sub-001_ses-LSD_task-rest_run-01_desc-confounds_timeseries.tsv",
        sep="\t",
        index=False,
    )

    payload = build_fmriprep_motion_proof_plan(tmp_path)

    assert payload["analysis_status"] == "structured_subject_level_confounds_available"
    assert payload["fmriprep_motion_proof_ready"] is True
    assert payload["existing_motion_confounds"]["motion_analysis_ready"] is True


def test_fmriprep_motion_plan_accepts_authorized_external_confound_roots(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_dataset_description(repo_root, "derivative")
    external_root = tmp_path / "author_confounds"
    confound_dir = external_root / "sub-001" / "ses-LSD" / "func"
    confound_dir.mkdir(parents=True)
    pd.DataFrame({"framewise_displacement": [0.0, 0.1], "std_dvars": [1.0, 1.2]}).to_csv(
        confound_dir / "sub-001_ses-LSD_task-rest_run-01_desc-confounds_timeseries.tsv",
        sep="\t",
        index=False,
    )

    payload = build_fmriprep_motion_proof_plan(repo_root, roots=[external_root])

    assert payload["analysis_status"] == "structured_subject_level_confounds_available"
    assert payload["fmriprep_motion_proof_ready"] is True
    assert payload["existing_motion_confounds"]["motion_analysis_ready"] is True
    assert payload["existing_motion_confounds"]["configured_motion_roots"]


def test_fmriprep_motion_plan_can_be_preflight_ready_without_claiming_proof(tmp_path: Path) -> None:
    _write_dataset_description(tmp_path, "raw")
    bold_dir = tmp_path / "data" / "ds003059" / "sub-001" / "ses-LSD" / "func"
    anat_dir = tmp_path / "data" / "ds003059" / "sub-001" / "anat"
    bold_dir.mkdir(parents=True)
    anat_dir.mkdir(parents=True)
    (bold_dir / "sub-001_ses-LSD_task-rest_run-01_bold.nii.gz").write_bytes(b"not-a-real-nifti")
    (anat_dir / "sub-001_T1w.nii.gz").write_bytes(b"not-a-real-nifti")

    payload = build_fmriprep_motion_proof_plan(tmp_path, runtime_availability={"docker": True})

    assert payload["analysis_status"] == "ready_to_run_fmriprep_preprocessing"
    assert payload["fmriprep_preflight_ready"] is True
    assert payload["fmriprep_motion_proof_ready"] is False
    assert "Run fMRIPrep" in payload["next_action"]


def test_write_fmriprep_motion_plan_writes_json_and_markdown(tmp_path: Path) -> None:
    _write_dataset_description(tmp_path, "derivative")

    payload = write_fmriprep_motion_proof_plan(tmp_path)

    assert payload["source_path"] == "results/confound_controls/fmriprep_motion_proof_plan.json"
    assert payload["report_path"] == "results/confound_controls/fmriprep_motion_proof_plan.md"
    assert (tmp_path / payload["source_path"]).exists()
    assert "fMRIPrep Motion-Proof Preflight" in (tmp_path / payload["report_path"]).read_text(encoding="utf-8")
