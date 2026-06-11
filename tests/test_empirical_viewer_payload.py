from __future__ import annotations

import json
from pathlib import Path

from lsd_thesis.web.empirical_viewer import (
    RUN02_EXPLORATORY_CAVEAT,
    augment_empirical_viewer_with_run02,
    empirical_selector_is_invalid,
    load_dashboard_empirical_detail,
    load_empirical_viewer_detail,
    load_empirical_viewer_overview,
    paired_subject_run_index,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_empirical_viewer_pairs_safe_subject_runs_and_loads_details(tmp_path: Path) -> None:
    viewer = tmp_path / "results" / "stage_2" / "empirical_viewer"
    _write_json(viewer / "group_overview.json", {"default_subject": "missing", "default_run": "run-99"})
    _write_json(viewer / "subject_index.json", {"legacy": ["run-99"]})
    _write_json(viewer / "subject_views" / "sub-002_run-03.json", {"subject": "sub-002", "run": "run-03"})
    _write_json(viewer / "subject_views" / "sub-002_run-01.json", {"subject": "sub-002", "run": "run-01"})
    _write_json(viewer / "subject_views" / "../bad.json", {"ignored": True})

    assert empirical_selector_is_invalid("../../secret", "run-01") is True
    assert paired_subject_run_index(viewer) == {"sub-002": ["run-01", "run-03"]}

    overview = load_empirical_viewer_overview(viewer)

    assert overview is not None
    assert overview["subjects"] == ["sub-002"]
    assert overview["runs"] == ["run-01", "run-03"]
    assert overview["default_subject"] == "sub-002"
    assert overview["default_run"] == "run-01"
    assert overview["condition_labels"]["ses-PLCB"] == "Placebo"
    assert load_empirical_viewer_detail(viewer, "sub-002", "run-01") == {
        "subject": "sub-002",
        "run": "run-01",
    }
    assert load_empirical_viewer_detail(viewer, "../../secret", "run-01") is None


def test_run02_viewer_merge_and_dashboard_detail_are_guarded(tmp_path: Path) -> None:
    primary = {
        "subjects": ["sub-002"],
        "runs": ["run-01"],
        "default_subject": "sub-002",
        "default_run": "run-01",
        "subject_index": {"sub-002": ["run-01"]},
        "run_caveats": {},
    }
    run02_root = (
        tmp_path
        / "results"
        / "setting_seed"
        / "run02_extraction"
        / "stage_2_music"
        / "empirical_viewer"
    )
    _write_json(run02_root / "group_overview.json", {"default_subject": "sub-002", "default_run": "run-02"})
    _write_json(run02_root / "subject_views" / "sub-002_run-02.json", {"subject": "sub-002", "run": "run-02"})
    _write_json(
        tmp_path / "results" / "setting_seed" / "run02_extraction" / "data_audit" / "data_audit.json",
        {
            "run_02_analysis_ready": True,
            "run_02_files_present": True,
            "run_02_valid_file_count": 1,
            "run_02_expected_file_count": 1,
            "record_count": 1,
            "subject_count": 1,
            "motion_summaries_available": False,
            "motion_analysis_ready": False,
            "run_labels": {"run-02": "Music"},
        },
    )

    merged = augment_empirical_viewer_with_run02(primary, tmp_path)
    detail = load_dashboard_empirical_detail(tmp_path, "sub-002", "run-02")

    assert merged is not None
    assert merged["default_run"] == "run-02"
    assert merged["subject_index"]["sub-002"] == ["run-01", "run-02"]
    assert merged["run_labels"]["run-02"] == "Music (exploratory)"
    assert merged["run_caveats"]["run-02"] == RUN02_EXPLORATORY_CAVEAT
    assert merged["run_02_status"]["motion_summaries_available"] is False
    assert detail is not None
    assert detail["run_label"] == "Music (exploratory)"
    assert detail["run_caveat"] == RUN02_EXPLORATORY_CAVEAT
