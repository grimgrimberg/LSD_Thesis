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
    assert summary["percent_fd_above_threshold"] == 50.0
    assert summary["mean_dvars"] == 2.5
    assert summary["scrubbed_volume_count"] == 1


def test_motion_summary_reports_unavailable_without_confounds(tmp_path: Path) -> None:
    summary = build_motion_summary(roots=(tmp_path,))

    assert summary["status"] == "unavailable_not_found"
    assert summary["motion_files_present"] is False
    assert summary["motion_analysis_ready"] is False


def test_write_motion_outputs_writes_explicit_unavailable_status(tmp_path: Path) -> None:
    output_dir = tmp_path / "motion"

    summary = write_motion_outputs(output_dir=output_dir, roots=(tmp_path / "missing",))

    assert summary["status"] == "unavailable_not_found"
    assert json.loads((output_dir / "motion_summary.json").read_text(encoding="utf-8"))["status"] == "unavailable_not_found"
    assert "No structured motion/confounds files were found" in (output_dir / "motion_report.md").read_text(encoding="utf-8")
