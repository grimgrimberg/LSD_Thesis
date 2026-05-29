import json
from pathlib import Path

from lsd_thesis.module_dvars_controls import build_module_dvars_control_status, write_module_dvars_control_status


def _write_view(root: Path, subject: str, run: str, scale: float) -> None:
    path = root / "results" / "stage_2" / "empirical_viewer" / "subject_views" / f"{subject}_{run}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    placebo = [[scale + time * 0.1 * scale, scale + time * 0.2 * scale] for time in range(8)]
    lsd = [[scale + time * 0.2 * scale, scale + time * 0.3 * scale] for time in range(8)]
    path.write_text(
        json.dumps(
            {
                "subject": subject,
                "run": run,
                "delta_metrics": {
                    "transition_rate_delta": scale,
                    "integration_delta": scale * 0.5,
                },
                "conditions": {
                    "ses-PLCB": {"module_time_series": placebo},
                    "ses-LSD": {"module_time_series": lsd},
                },
            }
        ),
        encoding="utf-8",
    )


def test_module_dvars_control_fails_closed_without_timeseries(tmp_path: Path) -> None:
    status = build_module_dvars_control_status(tmp_path)

    assert status["analysis_status"] == "blocked_missing_subject_run_module_time_series"
    assert status["module_dvars_control_ready"] is False
    assert status["claim_status"] == "not_proven_module_dvars_control_missing"


def test_module_dvars_control_computes_association_and_exclusion_rows(tmp_path: Path) -> None:
    for index in range(1, 7):
        _write_view(tmp_path, f"sub-{index:03d}", "run-01", float(index))

    status = build_module_dvars_control_status(tmp_path)

    assert status["analysis_status"] == "implemented_module_dvars_censoring_sensitivity"
    assert status["module_dvars_control_ready"] is True
    assert status["subject_count"] == 6
    assert status["subject_run_count"] == 6
    assert status["association_rows"]
    assert status["high_burden_exclusion_rows"]
    assert status["unbalanced_condition_volume_records"] == 0


def test_write_module_dvars_control_status_writes_artifacts(tmp_path: Path) -> None:
    status = write_module_dvars_control_status(tmp_path)

    assert status["source_path"] == "results/confound_controls/module_dvars_control_status.json"
    assert (tmp_path / "results" / "confound_controls" / "module_dvars_control_status.json").exists()
    assert (tmp_path / "results" / "confound_controls" / "module_dvars_dynamic_associations.csv").exists()
