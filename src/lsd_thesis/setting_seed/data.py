from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal, cast

import numpy as np
import pandas as pd

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.data.ds003059 import DS003059_DEFAULT_RUNS, DS003059_MUSIC_RUNS
from lsd_thesis.setting_seed.motion import build_motion_summary, discover_motion_files
from lsd_thesis.utils import get_version_stamp, resolve_under

RUN_LABELS = {"run-01": "Rest1", "run-02": "Music", "run-03": "Rest3"}
SESSIONS = ("ses-LSD", "ses-PLCB")
REST_RUNS = ("run-01", "run-03")
MUSIC_RUN = "run-02"
MUSIC_EXCLUDED_SUBJECTS = ("sub-003", "sub-012", "sub-015")
MOTION_PATTERN = re.compile(r"(confound|motion|fd|dvars|censor|scrub|desc-confounds|regress)", re.IGNORECASE)
RUN02_EXTRACTION_COMMAND = (
    "uv run python scripts/run_pipeline.py stage2 --include-music "
    "--runs run-01 run-02 run-03 --stage2-output-dir results/setting_seed/run02_extraction/stage_2_music"
)
MOTION_SUMMARY_COMMAND = "uv run python scripts/run_setting_seed_motion_summary.py"


def _default_repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _default_stage_2_dir() -> Path:
    return _default_repo_root() / "results" / "stage_2"


DEFAULT_STAGE_2_DIR = _default_stage_2_dir()


def _condition_label(session: str) -> str:
    if session == "ses-LSD":
        return "LSD"
    if session == "ses-PLCB":
        return "PLCB"
    return session.replace("ses-", "")


def load_run_records(stage_2_dir: str | Path | None = None) -> list[dict[str, Any]]:
    stage_2_path = DEFAULT_STAGE_2_DIR if stage_2_dir is None else Path(stage_2_dir)
    records_path = stage_2_path / "empirical_run_summaries.json"
    if not records_path.exists():
        raise FileNotFoundError(f"Missing empirical run summary: {records_path}")
    raw_records = cast(list[dict[str, Any]], json.loads(records_path.read_text(encoding="utf-8")))
    return sorted(raw_records, key=lambda item: (str(item.get("subject")), str(item.get("session")), str(item.get("run"))))


def resolve_time_series_path(stage_2_dir: str | Path, record: dict[str, Any]) -> Path:
    raw_path = record.get("time_series_path")
    if not raw_path:
        subject = str(record.get("subject"))
        session = str(record.get("session"))
        run = str(record.get("run"))
        raw_path = Path("module_time_series") / f"{subject}_{session}_{run}_modules.npy"
    return resolve_under(stage_2_dir, str(raw_path))


def load_module_time_series(stage_2_dir: str | Path, record: dict[str, Any]) -> np.ndarray:
    path = resolve_time_series_path(stage_2_dir, record)
    if not path.exists():
        raise FileNotFoundError(f"Missing module time series for {record.get('subject')} {record.get('session')} {record.get('run')}: {path}")
    array = np.load(path)
    if array.ndim != 2 or array.shape[1] != len(MODULE_NAMES):
        raise ValueError(f"Expected [time, {len(MODULE_NAMES)}] module array at {path}, found {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError(f"Non-finite values found in module time series: {path}")
    return np.asarray(array, dtype=float)


def load_tidy_time_series(stage_2_dir: str | Path | None = None) -> pd.DataFrame:
    stage_2_path = DEFAULT_STAGE_2_DIR if stage_2_dir is None else Path(stage_2_dir)
    rows: list[dict[str, Any]] = []
    for record in load_run_records(stage_2_path):
        subject = str(record["subject"])
        session = str(record["session"])
        run = str(record["run"])
        array = load_module_time_series(stage_2_path, record)
        for time_index in range(array.shape[0]):
            for module_index, module in enumerate(MODULE_NAMES):
                rows.append(
                    {
                        "subject": subject,
                        "session": session,
                        "condition": _condition_label(session),
                        "run": run,
                        "run_label": RUN_LABELS.get(run, run),
                        "time": time_index,
                        "module": module,
                        "value": float(array[time_index, module_index]),
                    }
                )
    return pd.DataFrame(rows, columns=["subject", "session", "condition", "run", "run_label", "time", "module", "value"])


def load_tensor(stage_2_dir: str | Path | None = None) -> dict[str, Any]:
    stage_2_path = DEFAULT_STAGE_2_DIR if stage_2_dir is None else Path(stage_2_dir)
    records = load_run_records(stage_2_path)
    subjects = sorted({str(record["subject"]) for record in records})
    sessions = sorted({str(record["session"]) for record in records})
    runs = sorted({str(record["run"]) for record in records})
    first = load_module_time_series(stage_2_path, records[0])
    tensor = np.full((len(subjects), len(sessions), len(runs), first.shape[0], len(MODULE_NAMES)), np.nan, dtype=float)
    subject_index = {subject: index for index, subject in enumerate(subjects)}
    session_index = {session: index for index, session in enumerate(sessions)}
    run_index = {run: index for index, run in enumerate(runs)}
    for record in records:
        array = load_module_time_series(stage_2_path, record)
        tensor[subject_index[str(record["subject"])], session_index[str(record["session"])], run_index[str(record["run"])], :, :] = array
    return {
        "subjects": subjects,
        "sessions": sessions,
        "runs": runs,
        "modules": list(MODULE_NAMES),
        "tensor": tensor,
    }


def filter_subjects_for_analysis(subjects: list[str] | tuple[str, ...], analysis: Literal["rest", "music"]) -> list[str]:
    ordered = sorted(subjects)
    if analysis == "rest":
        return ordered
    return [subject for subject in ordered if subject not in MUSIC_EXCLUDED_SUBJECTS]


def detect_motion_summary_files(repo_root: str | Path | None = None, stage_2_dir: str | Path | None = None) -> list[str]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    found: list[str] = []
    for path in discover_motion_files(repo_root=root, stage_2_dir=stage_2_dir):
        try:
            found.append(path.resolve().relative_to(root.resolve()).as_posix())
        except ValueError:
            found.append(path.name)
    return sorted(found)


def audit_stage2_cache(
    stage_2_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    stage_2_path = DEFAULT_STAGE_2_DIR if stage_2_dir is None else Path(stage_2_dir)
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    records = load_run_records(stage_2_path)
    subjects = sorted({str(record["subject"]) for record in records})
    sessions = sorted({str(record["session"]) for record in records})
    runs = sorted({str(record["run"]) for record in records})
    shapes: dict[str, list[int]] = {}
    missing_files: list[str] = []
    invalid_shapes: list[dict[str, Any]] = []
    for record in records:
        key = f"{record['subject']}_{record['session']}_{record['run']}"
        try:
            array = load_module_time_series(stage_2_path, record)
        except FileNotFoundError:
            missing_files.append(key)
            continue
        shapes[key] = list(array.shape)
        if array.shape[1] != len(MODULE_NAMES):
            invalid_shapes.append({"record": key, "shape": list(array.shape)})

    observed_keys = {
        (str(record["subject"]), str(record["session"]), str(record["run"]))
        for record in records
    }
    complete_rest_subjects = sorted(
        subject
        for subject in subjects
        if all((subject, session, run) in observed_keys for session in SESSIONS for run in REST_RUNS)
    )
    run_02_files = sorted((stage_2_path / "module_time_series").glob("*run-02*_modules.npy"))
    run_02_records = [record for record in records if str(record.get("run")) == MUSIC_RUN]
    expected_music_subjects = filter_subjects_for_analysis(subjects, analysis="music")
    expected_run_02_keys = [(subject, session) for subject in expected_music_subjects for session in SESSIONS]
    present_run_02_keys = {
        (str(record["subject"]), str(record["session"]))
        for record in run_02_records
        if str(record.get("subject")) not in MUSIC_EXCLUDED_SUBJECTS
    }
    run_02_missing_subject_session = [
        {"subject": subject, "session": session}
        for subject, session in expected_run_02_keys
        if (subject, session) not in present_run_02_keys
    ]
    run_02_valid_file_count = 0
    for record in run_02_records:
        if str(record.get("subject")) in MUSIC_EXCLUDED_SUBJECTS:
            continue
        try:
            load_module_time_series(stage_2_path, record)
        except (FileNotFoundError, ValueError):
            continue
        run_02_valid_file_count += 1
    run_02_files_present = bool(run_02_files or run_02_records)
    run_02_analysis_ready = bool(
        expected_run_02_keys
        and run_02_files_present
        and run_02_valid_file_count >= len(expected_run_02_keys)
        and not run_02_missing_subject_session
    )
    motion_summary = build_motion_summary(repo_root=root, stage_2_dir=stage_2_path)
    motion_files = cast(list[str], motion_summary.get("motion_summary_files", []))
    motion_files_present = bool(motion_summary.get("motion_files_present"))
    motion_analysis_ready = bool(motion_summary.get("motion_analysis_ready"))
    blockers: list[str] = []
    if not run_02_files_present:
        blockers.append("run-02 module time series are missing; music-control empirical analysis is scaffolded only.")
    elif not run_02_analysis_ready:
        blockers.append("run-02 module time series are present but incomplete for music-eligible subject/session coverage.")
    if not motion_analysis_ready:
        blockers.append("subject-level motion summaries are missing; motion sensitivity is unavailable.")
    music_control_status = "ready_descriptive_only"
    if not run_02_files_present:
        music_control_status = "blocked_missing_run_02"
    elif not run_02_analysis_ready:
        music_control_status = "blocked_incomplete_run_02"
    elif not motion_analysis_ready:
        music_control_status = "blocked_missing_motion_review"

    return {
        "schema_version": "setting_seed_data_audit.v1",
        "source": "cached_stage_2_module_time_series",
        "stage_2_dir": str(stage_2_path),
        "record_count": len(records),
        "subjects": subjects,
        "subject_count": len(subjects),
        "complete_rest_subjects": complete_rest_subjects,
        "sessions": sessions,
        "runs": runs,
        "run_labels": dict(RUN_LABELS),
        "modules": list(MODULE_NAMES),
        "module_count": len(MODULE_NAMES),
        "time_series_shapes": shapes,
        "missing_time_series_files": missing_files,
        "invalid_shapes": invalid_shapes,
        "run_02_available": bool(run_02_files),
        "run_02_extraction_support_available": True,
        "run_02_default_runs": list(DS003059_DEFAULT_RUNS),
        "run_02_supported_runs": list(DS003059_MUSIC_RUNS),
        "run_02_files_present": run_02_files_present,
        "run_02_analysis_ready": run_02_analysis_ready,
        "run_02_expected_file_count": len(expected_run_02_keys),
        "run_02_valid_file_count": run_02_valid_file_count,
        "run_02_missing_subject_session": run_02_missing_subject_session,
        "run_02_file_count": len(run_02_files),
        "motion_summaries_available": bool(motion_files),
        "motion_summary_support_available": True,
        "motion_files_present": motion_files_present,
        "motion_summary_schema_valid": bool(motion_summary.get("motion_summary_schema_valid")),
        "motion_coverage_by_run": motion_summary.get("coverage_by_run", {}),
        "motion_analysis_ready": motion_analysis_ready,
        "motion_summary_files": motion_files,
        "music_excluded_subjects": list(MUSIC_EXCLUDED_SUBJECTS),
        "music_exclusion_enforced": True,
        "music_analysis_subject_count": len(expected_music_subjects),
        "rest_only_subjects": filter_subjects_for_analysis(subjects, analysis="rest"),
        "music_eligible_subjects": expected_music_subjects,
        "analysis_availability": {
            "rest_reliability": "available" if {"run-01", "run-03"}.issubset(set(runs)) else "blocked_missing_rest_runs",
            "latent_rest_geometry": "available" if {"run-01", "run-03"}.issubset(set(runs)) else "blocked_missing_rest_runs",
            "music_control": music_control_status,
            "motion_sensitivity": "available" if motion_analysis_ready else "unavailable_missing_motion_summaries",
        },
        "next_commands": {
            "run_02_extraction_after_approval": RUN02_EXTRACTION_COMMAND,
            "motion_summary": MOTION_SUMMARY_COMMAND,
        },
        "blockers": blockers,
        "claim_guardrail": "Data audit is an implemented cache inventory, not evidence for music-control or motion-controlled effects.",
        "version_stamp": get_version_stamp(root),
    }


def audit_to_markdown(audit: dict[str, Any]) -> str:
    subjects = ", ".join(cast(list[str], audit["subjects"]))
    return "\n".join(
        [
            "# Set / Setting / Seed Data Audit",
            "",
            "Status: implemented cache inventory.",
            "",
            f"- Subjects found: {audit['subject_count']} ({subjects})",
            f"- Sessions found: {', '.join(cast(list[str], audit['sessions']))}",
            f"- Runs found: {', '.join(cast(list[str], audit['runs']))}",
            f"- Modules found: {', '.join(cast(list[str], audit['modules']))}",
            f"- Run-02 extraction support available: {str(audit['run_02_extraction_support_available']).lower()}",
            f"- Run-02 data present: {str(audit['run_02_files_present']).lower()}",
            f"- Run-02 analysis ready: {str(audit['run_02_analysis_ready']).lower()}",
            f"- Motion-summary support available: {str(audit['motion_summary_support_available']).lower()}",
            f"- Motion summaries present: {str(audit['motion_files_present']).lower()}",
            f"- Motion analysis ready: {str(audit['motion_analysis_ready']).lower()}",
            f"- Music-control empirical analysis: {audit['analysis_availability']['music_control']}",
            f"- Rest-only reliability and latent analyses: {audit['analysis_availability']['rest_reliability']}",
            f"- Run-02 command after approval: `{audit['next_commands']['run_02_extraction_after_approval']}`",
            f"- Motion summary command: `{audit['next_commands']['motion_summary']}`",
            "",
            "## Guardrails",
            "",
            "- Music-control analysis is scaffolded only until run-02 module time series are extracted.",
            "- S03, S12, and S15 are excluded only from future music-specific analyses.",
            "- Motion sensitivity is unavailable because no subject/run-level motion summaries are cached.",
            "- This audit does not mutate legacy Stage 1-5 outputs.",
            "",
            "## Blockers",
            "",
            *[f"- {blocker}" for blocker in cast(list[str], audit["blockers"])],
            "",
        ]
    )


def write_data_audit(
    stage_2_dir: str | Path | None = None,
    output_dir: str | Path | None = None,
    repo_root: str | Path | None = None,
) -> dict[str, Any]:
    root = _default_repo_root() if repo_root is None else Path(repo_root)
    out_dir = root / "results" / "setting_seed" / "data_audit" if output_dir is None else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_stage2_cache(stage_2_dir=stage_2_dir, repo_root=root)
    (out_dir / "data_audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
    (out_dir / "data_audit.md").write_text(audit_to_markdown(audit), encoding="utf-8")
    return audit
