import json
from pathlib import Path

from lsd_thesis.design_confound_controls import build_design_confound_control_status, write_design_confound_control_status


def _write_view(root: Path, subject: str, run: str, metric_value: float) -> None:
    path = root / "results" / "stage_2" / "empirical_viewer" / "subject_views" / f"{subject}_{run}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "subject": subject,
                "run": run,
                "delta_metrics": {
                    "transition_rate_delta": metric_value,
                    "integration_delta": metric_value * 0.5,
                },
                "conditions": {
                    "ses-PLCB": {"window_count": 6, "global_signal": [1.0, 1.1, 1.2]},
                    "ses-LSD": {"window_count": 6, "global_signal": [1.2, 1.3, 1.4]},
                },
            }
        ),
        encoding="utf-8",
    )


def test_design_confound_control_fails_closed_without_subject_views(tmp_path: Path) -> None:
    status = build_design_confound_control_status(tmp_path)

    assert status["analysis_status"] == "blocked_missing_primary_empirical_viewer_subject_views"
    assert status["design_confound_control_ready"] is False
    assert status["claim_status"] == "not_proven_design_confound_control_missing"


def test_design_confound_control_computes_paired_run_sensitivity(tmp_path: Path) -> None:
    for index in range(1, 7):
        subject = f"sub-{index:03d}"
        _write_view(tmp_path, subject, "run-01", float(index))
        _write_view(tmp_path, subject, "run-03", float(index) + 0.05)

    status = build_design_confound_control_status(tmp_path)

    assert status["analysis_status"] == "implemented_design_confound_control_result"
    assert status["design_confound_control_ready"] is True
    assert status["subject_count"] == 6
    assert status["run_count"] == 2
    assert status["paired_run_tests"]
    assert status["window_count_summary"]["unbalanced_record_count"] == 0


def test_write_design_confound_control_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_design_confound_control_status(tmp_path)

    assert status["source_path"] == "results/confound_controls/design_confound_control_status.json"
    assert (tmp_path / "results" / "confound_controls" / "design_confound_control_status.json").exists()
    assert (tmp_path / "results" / "confound_controls" / "design_confound_control_status.md").exists()
