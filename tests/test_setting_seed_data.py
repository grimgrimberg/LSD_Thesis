import json
import uuid
from pathlib import Path

import numpy as np

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.setting_seed.data import (
    MUSIC_EXCLUDED_SUBJECTS,
    audit_stage2_cache,
    filter_subjects_for_analysis,
    load_tidy_time_series,
)


def _fixture_root(name: str) -> Path:
    root = Path("results") / "setting_seed" / "test_fixtures" / f"{name}_{uuid.uuid4().hex}"
    root.mkdir(parents=True)
    return root


def _write_stage2_fixture(name: str, *, include_music: bool = False) -> Path:
    fixture_root = _fixture_root(name)
    stage_2 = fixture_root / "stage_2"
    series_dir = stage_2 / "module_time_series"
    series_dir.mkdir(parents=True)
    records: list[dict[str, object]] = []
    for subject in ["sub-003", "sub-001"]:
        for session in ["ses-PLCB", "ses-LSD"]:
            runs = ["run-03", "run-01", "run-02"] if include_music else ["run-03", "run-01"]
            for run in runs:
                file_name = f"{subject}_{session}_{run}_modules.npy"
                values = np.arange(4 * len(MODULE_NAMES), dtype=float).reshape(4, len(MODULE_NAMES))
                np.save(series_dir / file_name, values)
                records.append(
                    {
                        "subject": subject,
                        "session": session,
                        "run": run,
                        "relative_path": f"{subject}/{session}/func/{file_name}",
                        "timepoints": 4,
                        "time_series_path": str(Path("module_time_series") / file_name),
                        "metrics": {"cross_network_communication": float(values.mean())},
                    }
                )
    (stage_2 / "empirical_run_summaries.json").write_text(json.dumps(records), encoding="utf-8")
    return stage_2


def test_audit_stage2_cache_reports_deterministic_rest_coverage_and_missing_music() -> None:
    stage_2 = _write_stage2_fixture("data_audit")
    fixture_root = stage_2.parent

    audit = audit_stage2_cache(stage_2_dir=stage_2, repo_root=fixture_root)

    assert audit["subjects"] == ["sub-001", "sub-003"]
    assert audit["sessions"] == ["ses-LSD", "ses-PLCB"]
    assert audit["runs"] == ["run-01", "run-03"]
    assert audit["run_labels"] == {"run-01": "Rest1", "run-02": "Music", "run-03": "Rest3"}
    assert audit["modules"] == list(MODULE_NAMES)
    assert audit["run_02_available"] is False
    assert audit["run_02_extraction_support_available"] is True
    assert audit["run_02_files_present"] is False
    assert audit["run_02_analysis_ready"] is False
    assert audit["motion_summaries_available"] is False
    assert audit["motion_summary_support_available"] is True
    assert audit["motion_files_present"] is False
    assert audit["motion_analysis_ready"] is False
    assert audit["analysis_availability"]["rest_reliability"] == "available"
    assert audit["analysis_availability"]["music_control"] == "blocked_missing_run_02"
    assert audit["music_excluded_subjects"] == list(MUSIC_EXCLUDED_SUBJECTS)
    assert "--include-music" in audit["next_commands"]["run_02_extraction_after_approval"]


def test_music_exclusions_apply_only_to_music_specific_analysis() -> None:
    stage_2 = _write_stage2_fixture("music_exclusions")
    fixture_root = stage_2.parent
    audit = audit_stage2_cache(stage_2_dir=stage_2, repo_root=fixture_root)

    rest_subjects = filter_subjects_for_analysis(audit["subjects"], analysis="rest")
    music_subjects = filter_subjects_for_analysis(audit["subjects"], analysis="music")

    assert "sub-003" in rest_subjects
    assert "sub-003" not in music_subjects
    assert "sub-001" in music_subjects


def test_complete_rest_subjects_remain_complete_when_music_run_is_present() -> None:
    stage_2 = _write_stage2_fixture("rest_plus_music", include_music=True)
    fixture_root = stage_2.parent

    audit = audit_stage2_cache(stage_2_dir=stage_2, repo_root=fixture_root)

    assert audit["runs"] == ["run-01", "run-02", "run-03"]
    assert audit["complete_rest_subjects"] == ["sub-001", "sub-003"]
    assert audit["run_02_files_present"] is True
    assert audit["run_02_valid_file_count"] == 2
    assert audit["run_02_analysis_ready"] is True
    assert audit["analysis_availability"]["music_control"] == "blocked_missing_motion_review"


def test_load_tidy_time_series_preserves_module_order() -> None:
    stage_2 = _write_stage2_fixture("tidy")

    tidy = load_tidy_time_series(stage_2)

    assert list(tidy.columns) == ["subject", "session", "condition", "run", "run_label", "time", "module", "value"]
    assert tidy["subject"].drop_duplicates().tolist() == ["sub-001", "sub-003"]
    assert tidy["module"].drop_duplicates().tolist() == list(MODULE_NAMES)
    assert set(tidy["run_label"]) == {"Rest1", "Rest3"}


def test_data_audit_json_schema_has_explicit_blockers() -> None:
    stage_2 = _write_stage2_fixture("schema")
    fixture_root = stage_2.parent

    audit = audit_stage2_cache(stage_2_dir=stage_2, repo_root=fixture_root)

    assert audit["schema_version"] == "setting_seed_data_audit.v1"
    assert audit["blockers"] == [
        "run-02 module time series are missing; music-control empirical analysis is scaffolded only.",
        "subject-level motion summaries are missing; motion sensitivity is unavailable.",
    ]
    assert audit["rest_only_subjects"] == ["sub-001", "sub-003"]
    assert audit["music_eligible_subjects"] == ["sub-001"]
