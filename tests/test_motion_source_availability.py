from __future__ import annotations

from pathlib import Path

from lsd_thesis.motion_source_availability import build_motion_source_availability


def test_motion_source_availability_reports_absent_remote_sources(tmp_path: Path) -> None:
    payload = build_motion_source_availability(
        tmp_path,
        openneuro_files=[
            {"filename": "sub-001/ses-LSD/func/sub-001_ses-LSD_task-rest_bold.nii.gz", "directory": False},
            {"filename": "README", "directory": False},
        ],
        derivative_repo_statuses=[
            {"url": "https://example.test/fmriprep", "status_code": 404, "available": False},
            {"url": "https://example.test/mriqc", "status_code": 404, "available": False},
        ],
    )

    assert payload["analysis_status"] == "no_authorized_subject_level_motion_confounds_found"
    assert payload["source_confounds_available"] is False
    assert payload["openneuro_raw_snapshot"]["file_count"] == 2
    assert payload["openneuro_raw_snapshot"]["confound_like_file_count"] == 0
    assert payload["public_derivative_repositories"]["available_count"] == 0


def test_motion_source_availability_detects_local_confounds(tmp_path: Path) -> None:
    confounds = tmp_path / "data" / "ds003059" / "derivatives" / "fmriprep" / "sub-001" / "ses-LSD" / "func"
    confounds.mkdir(parents=True)
    (confounds / "sub-001_ses-LSD_task-rest_run-01_desc-confounds_timeseries.tsv").write_text(
        "framewise_displacement\tstd_dvars\n0.0\t1.0\n",
        encoding="utf-8",
    )

    payload = build_motion_source_availability(tmp_path)

    assert payload["analysis_status"] == "authorized_subject_level_motion_confounds_available"
    assert payload["source_confounds_available"] is True
    assert payload["local_search"]["motion_file_count"] == 1
