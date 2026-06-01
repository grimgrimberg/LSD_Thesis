import json
from pathlib import Path

import pandas as pd

from lsd_thesis.setting_seed.motion import build_motion_summary, summarize_motion_tsv, write_motion_outputs


def test_summarize_motion_tsv_parses_fd_dvars_and_scrub_columns(tmp_path: Path) -> None:
    path = tmp_path / "sub-001_ses-LSD_task-rest_run-01_desc-confounds_timeseries.tsv"
    pd.DataFrame(
        {
            "framewise_displacement": [0.0, 0.2, 0.6, 1.0],
            "std_dvars": [1.0, 2.0, 3.0, 4.0],
            "motion_outlier00": [0, 0, 1, 0],
        }
    ).to_csv(path, sep="\t", index=False)

    summary = summarize_motion_tsv(path, fd_threshold=0.5)

    assert summary["status"] == "available_parsed"
    assert summary["subject"] == "sub-001"
    assert summary["session"] == "ses-LSD"
    assert summary["run"] == "run-01"
    assert summary["mean_fd"] == 0.45
    assert summary["max_fd"] == 1.0
    assert summary["fd_spike_fraction"] == 0.5
    assert summary["percent_fd_above_threshold"] == 50.0
    assert summary["mean_dvars"] == 2.5
    assert summary["scrubbed_volume_count"] == 1
    assert summary["motion_outlier_fraction"] == 0.25


def test_motion_summary_reports_unavailable_without_confounds(tmp_path: Path) -> None:
    summary = build_motion_summary(roots=(tmp_path,))

    assert summary["status"] == "unavailable_not_found"
    assert summary["motion_files_present"] is False
    assert summary["motion_analysis_ready"] is False
    assert summary["input_contract"]["expected_file_patterns"]
    assert "framewise_displacement or fd" in summary["input_contract"]["required_columns"]
    assert "subject id" in summary["input_contract"]["minimum_pairing_contract"]


def test_motion_summary_rejects_confounds_without_pairing_metadata(tmp_path: Path) -> None:
    pd.DataFrame({"framewise_displacement": [0.0, 0.1], "std_dvars": [1.0, 1.1]}).to_csv(
        tmp_path / "desc-confounds_timeseries.tsv",
        sep="\t",
        index=False,
    )

    summary = build_motion_summary(roots=(tmp_path,))

    assert summary["status"] == "found_unusable"
    assert summary["motion_files_present"] is True
    assert summary["motion_analysis_ready"] is False
    assert summary["parsed_summary_count"] == 0
    assert summary["unusable_file_count"] == 1
    assert summary["summaries"][0]["reason"] == "missing_subject_session_or_run_metadata"


def test_motion_summary_requires_paired_lsd_placebo_subject_run_coverage(tmp_path: Path) -> None:
    for index in range(4):
        subject = f"sub-{index + 1:03d}"
        for session in ("ses-LSD", "ses-PLCB"):
            path = tmp_path / subject / session / "func" / f"{subject}_{session}_task-rest_run-01_desc-confounds_timeseries.tsv"
            path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(
                {
                    "framewise_displacement": [0.0, 0.1],
                    "std_dvars": [1.0, 1.1],
                    "motion_outlier00": [0, 1],
                }
            ).to_csv(path, sep="\t", index=False)

    summary = build_motion_summary(roots=(tmp_path,))

    assert summary["motion_analysis_ready"] is True
    assert summary["motion_pairing_ready"] is True
    assert summary["paired_subject_run_count"] == 4
    assert len(summary["condition_coverage_by_subject_run"]) == 4


def test_motion_summary_keeps_unpaired_confounds_below_strict_pairing_threshold(tmp_path: Path) -> None:
    path = tmp_path / "sub-001" / "ses-LSD" / "func" / "sub-001_ses-LSD_task-rest_run-01_desc-confounds_timeseries.tsv"
    path.parent.mkdir(parents=True)
    pd.DataFrame({"framewise_displacement": [0.0, 0.1], "std_dvars": [1.0, 1.1]}).to_csv(
        path,
        sep="\t",
        index=False,
    )

    summary = build_motion_summary(roots=(tmp_path,))

    assert summary["motion_analysis_ready"] is True
    assert summary["motion_pairing_ready"] is False
    assert summary["paired_subject_run_count"] == 0
    assert "Add paired LSD and placebo/PLCB confounds" in summary["next_action"]


def test_summarize_motion_tsv_accepts_constant_pairing_columns(tmp_path: Path) -> None:
    path = tmp_path / "desc-confounds_timeseries.tsv"
    pd.DataFrame(
        {
            "participant_id": ["sub-001", "sub-001"],
            "condition": ["ses-LSD", "ses-LSD"],
            "run": ["run-01", "run-01"],
            "framewise_displacement": [0.0, 0.1],
            "std_dvars": [1.0, 1.1],
        }
    ).to_csv(path, sep="\t", index=False)

    summary = summarize_motion_tsv(path)

    assert summary["status"] == "available_parsed"
    assert summary["subject"] == "sub-001"
    assert summary["session"] == "ses-LSD"
    assert summary["run"] == "run-01"


def test_summarize_motion_tsv_normalizes_shorthand_pairing_columns(tmp_path: Path) -> None:
    path = tmp_path / "author_motion_desc-confounds_timeseries.tsv"
    pd.DataFrame(
        {
            "participant_id": ["1", "1"],
            "condition": ["LSD", "LSD"],
            "run": ["1", "1"],
            "framewise_displacement": [0.0, 0.1],
            "std_dvars": [1.0, 1.1],
        }
    ).to_csv(path, sep="\t", index=False)

    summary = summarize_motion_tsv(path)

    assert summary["status"] == "available_parsed"
    assert summary["subject"] == "sub-001"
    assert summary["session"] == "ses-LSD"
    assert summary["run"] == "run-01"


def test_write_motion_outputs_writes_explicit_unavailable_status(tmp_path: Path) -> None:
    output_dir = tmp_path / "motion"

    summary = write_motion_outputs(output_dir=output_dir, roots=(tmp_path / "missing",))

    assert summary["status"] == "unavailable_not_found"
    assert json.loads((output_dir / "motion_summary.json").read_text(encoding="utf-8"))["status"] == "unavailable_not_found"
    assert "No structured motion/confounds files were found" in (output_dir / "motion_report.md").read_text(encoding="utf-8")
    assert "Required local input contract" in (output_dir / "motion_report.md").read_text(encoding="utf-8")
