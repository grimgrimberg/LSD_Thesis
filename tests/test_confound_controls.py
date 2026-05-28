import json
from pathlib import Path

from lsd_thesis.confound_controls import build_motion_confound_control_status, write_motion_confound_control_status


def test_motion_confound_control_fails_closed_without_motion_summary(tmp_path: Path) -> None:
    status = build_motion_confound_control_status(tmp_path)

    assert status["analysis_status"] == "blocked_missing_motion_summaries"
    assert status["motion_confound_control_ready"] is False
    assert status["claim_status"] == "not_proven_motion_confound_control_missing"


def test_motion_confound_control_computes_subject_run_associations(tmp_path: Path) -> None:
    motion_dir = tmp_path / "results" / "setting_seed" / "motion"
    views_dir = tmp_path / "results" / "stage_2" / "empirical_viewer" / "subject_views"
    motion_dir.mkdir(parents=True)
    views_dir.mkdir(parents=True)
    summaries = []
    for index in range(6):
        subject = f"sub-{index + 1:03d}"
        run = "run-01"
        summaries.append(
            {
                "subject": subject,
                "session": "ses-PLCB",
                "run": run,
                "framewise_displacement_mean": 0.05,
                "framewise_displacement_max": 0.10,
                "std_dvars_mean": 0.20,
            }
        )
        summaries.append(
            {
                "subject": subject,
                "session": "ses-LSD",
                "run": run,
                "framewise_displacement_mean": 0.05 + index * 0.02,
                "framewise_displacement_max": 0.10 + index * 0.03,
                "std_dvars_mean": 0.20 + index * 0.01,
            }
        )
        (views_dir / f"{subject}_{run}.json").write_text(
            json.dumps(
                {
                    "subject": subject,
                    "run": run,
                    "delta_metrics": {
                        "cross_network_communication": 0.3 - index * 0.01,
                        "within_network_stability": 0.1 + index * 0.04,
                    },
                }
            ),
            encoding="utf-8",
        )
    (motion_dir / "motion_summary.json").write_text(
        json.dumps(
            {
                "status": "available_parsed",
                "motion_analysis_ready": True,
                "motion_files_present": True,
                "summaries": summaries,
            }
        ),
        encoding="utf-8",
    )

    status = build_motion_confound_control_status(tmp_path)

    assert status["analysis_status"] == "implemented_dedicated_motion_confound_control_result"
    assert status["motion_confound_control_ready"] is True
    assert status["merged_subject_run_count"] == 6
    assert status["association_rows"]
    assert any(row["motion_feature"] == "fd_mean_delta_lsd_minus_placebo" for row in status["association_rows"])


def test_write_motion_confound_control_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_motion_confound_control_status(tmp_path)

    assert status["source_path"] == "results/confound_controls/motion_confound_control_status.json"
    assert (tmp_path / status["source_path"]).exists()
    assert (tmp_path / status["report_path"]).exists()
    assert (tmp_path / status["association_csv_path"]).exists()
