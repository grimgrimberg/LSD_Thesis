from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, cast

SAFE_EMPIRICAL_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
RUN02_VIEWER_RELATIVE_PARTS = (
    "results",
    "setting_seed",
    "run02_extraction",
    "stage_2_music",
    "empirical_viewer",
)
RUN02_DATA_AUDIT_RELATIVE_PARTS = (
    "results",
    "setting_seed",
    "run02_extraction",
    "data_audit",
    "data_audit.json",
)
RUN02_EXPLORATORY_CAVEAT = (
    "Run-02 is the music run from the guarded extraction. Motion summaries are unavailable, "
    "so use it for exploratory inspection only, not primary or motion-sensitive claims."
)


def is_safe_empirical_selector(value: str) -> bool:
    return bool(SAFE_EMPIRICAL_ID_RE.fullmatch(value))


def empirical_selector_is_invalid(subject: str, run: str) -> bool:
    return not (is_safe_empirical_selector(subject) and is_safe_empirical_selector(run))


def load_empirical_viewer_overview(viewer_root: Path) -> dict[str, Any] | None:
    group_overview_path = viewer_root / "group_overview.json"
    subject_index_path = viewer_root / "subject_index.json"
    if not group_overview_path.exists():
        return None
    overview = cast(dict[str, Any], json.loads(group_overview_path.read_text(encoding="utf-8")))
    if subject_index_path.exists():
        overview["subject_index"] = cast(
            dict[str, Any], json.loads(subject_index_path.read_text(encoding="utf-8"))
        )
    paired_run_index = paired_subject_run_index(viewer_root)
    if paired_run_index:
        paired_subjects = sorted(paired_run_index)
        paired_runs = sorted({run for runs in paired_run_index.values() for run in runs})
        overview["subjects"] = paired_subjects
        overview["runs"] = paired_runs
        overview["subject_index"] = paired_run_index
        overview["paired_run_index"] = paired_run_index
        overview["available_pair_count"] = sum(len(runs) for runs in paired_run_index.values())
        if overview.get("default_subject") not in paired_run_index:
            overview["default_subject"] = paired_subjects[0]
    overview.setdefault(
        "display_metadata",
        {
            "preview_kind": "window_averaged_downsampled_slice_preview",
            "preview_normalization": "plane-wise min-max display normalization",
            "window_aggregation": "mean over the selected time window",
            "time_axis_units": "resampled index",
            "claim_guardrail": (
                "Empirical viewer panels are descriptive within-dataset proxy summaries, "
                "not diagnostic images or subjective-state validation."
            ),
        },
    )
    overview.setdefault("condition_labels", {"ses-PLCB": "Placebo", "ses-LSD": "LSD"})
    return overview


def paired_subject_run_index(viewer_root: Path) -> dict[str, list[str]]:
    subject_views_dir = viewer_root / "subject_views"
    if not subject_views_dir.exists():
        return {}
    subject_index: dict[str, list[str]] = {}
    for detail_path in sorted(subject_views_dir.glob("*.json")):
        if not detail_path.is_file() or "_" not in detail_path.stem:
            continue
        subject, run = detail_path.stem.rsplit("_", 1)
        if not (is_safe_empirical_selector(subject) and is_safe_empirical_selector(run)):
            continue
        subject_index.setdefault(subject, []).append(run)
    return {subject: sorted(runs) for subject, runs in sorted(subject_index.items())}


def load_empirical_viewer_detail(
    viewer_root: Path,
    subject: str,
    run: str,
) -> dict[str, Any] | None:
    if not is_safe_empirical_selector(subject) or not is_safe_empirical_selector(run):
        return None
    subject_views_dir = (viewer_root / "subject_views").resolve()
    detail_path = (subject_views_dir / f"{subject}_{run}.json").resolve()
    try:
        detail_path.relative_to(subject_views_dir)
    except ValueError:
        return None
    if not detail_path.exists():
        return None
    return cast(dict[str, Any], json.loads(detail_path.read_text(encoding="utf-8")))


def run02_viewer_root(repo_root: Path) -> Path:
    return repo_root.joinpath(*RUN02_VIEWER_RELATIVE_PARTS)


def run02_data_audit_path(repo_root: Path) -> Path:
    return repo_root.joinpath(*RUN02_DATA_AUDIT_RELATIVE_PARTS)


def _run_sort_key(run: str) -> tuple[int, int, str]:
    match = re.fullmatch(r"run-(\d+)", run)
    if match:
        return (0, int(match.group(1)), run)
    return (1, 0, run)


def _sorted_runs(runs: list[str] | set[str]) -> list[str]:
    return sorted(set(runs), key=_run_sort_key)


def load_run02_data_audit(repo_root: Path) -> dict[str, Any]:
    data_audit_path = run02_data_audit_path(repo_root)
    if not data_audit_path.exists():
        return {}
    return cast(dict[str, Any], json.loads(data_audit_path.read_text(encoding="utf-8")))


def _friendly_run_label(label: Any, run: str) -> str:
    if not isinstance(label, str) or not label:
        return run
    label_map = {
        "Rest1": "Rest 1",
        "Rest3": "Rest 3",
        "Music": "Music (exploratory)",
    }
    return label_map.get(label, label)


def run02_status(repo_root: Path, viewer_root: Path) -> dict[str, Any]:
    audit = load_run02_data_audit(repo_root)
    analysis_status = cast(dict[str, Any], audit.get("analysis_status") or {})
    return {
        "available": viewer_root.exists(),
        "analysis_ready": audit.get("run_02_analysis_ready"),
        "files_present": audit.get("run_02_files_present"),
        "valid_file_count": audit.get("run_02_valid_file_count"),
        "expected_file_count": audit.get("run_02_expected_file_count"),
        "record_count": audit.get("record_count"),
        "subject_count": audit.get("subject_count"),
        "music_control": analysis_status.get("music_control"),
        "motion_summaries_available": audit.get("motion_summaries_available"),
        "motion_analysis_ready": audit.get("motion_analysis_ready"),
        "source_path": viewer_root.relative_to(repo_root).as_posix(),
        "data_audit_path": run02_data_audit_path(repo_root).relative_to(repo_root).as_posix(),
        "claim_guardrail": audit.get("claim_guardrail") or RUN02_EXPLORATORY_CAVEAT,
    }


def augment_empirical_viewer_with_run02(
    overview: dict[str, Any] | None,
    repo_root: Path,
) -> dict[str, Any] | None:
    if overview is None:
        return None
    viewer_root = run02_viewer_root(repo_root)
    run02_overview = load_empirical_viewer_overview(viewer_root)
    if run02_overview is None:
        return overview

    run02_subject_index = cast(dict[str, Any], run02_overview.get("subject_index") or {})
    subjects_with_run02 = {
        str(subject)
        for subject, runs in run02_subject_index.items()
        if isinstance(runs, list) and "run-02" in runs
    }
    if not subjects_with_run02:
        return overview

    merged = dict(overview)
    primary_subject_index = cast(dict[str, Any], merged.get("subject_index") or {})
    subject_index: dict[str, list[str]] = {}
    for subject, runs in primary_subject_index.items():
        if not isinstance(runs, list):
            continue
        subject_index[str(subject)] = _sorted_runs([str(run) for run in runs])

    for subject in subjects_with_run02:
        subject_index.setdefault(subject, [])
        if "run-02" not in subject_index[subject]:
            subject_index[subject].append("run-02")
        subject_index[subject] = _sorted_runs(subject_index[subject])

    merged["subjects"] = sorted(subject_index)
    merged["runs"] = _sorted_runs([str(run) for run in merged.get("runs", [])] + ["run-02"])
    merged["default_run"] = "run-02"
    merged["subject_index"] = subject_index
    merged["paired_run_index"] = subject_index
    merged["available_pair_count"] = sum(len(runs) for runs in subject_index.values())
    if merged.get("default_subject") not in subject_index and subject_index:
        merged["default_subject"] = sorted(subject_index)[0]

    audit = load_run02_data_audit(repo_root)
    audit_run_labels = cast(dict[str, Any], audit.get("run_labels") or {})
    existing_labels = cast(dict[str, Any], merged.get("run_labels") or {})
    run_labels = {str(run): _friendly_run_label(label, str(run)) for run, label in audit_run_labels.items()}
    run_labels.update({str(run): str(label) for run, label in existing_labels.items()})
    run_labels["run-02"] = "Music (exploratory)"
    merged["run_labels"] = run_labels

    run_caveats = {str(run): str(caveat) for run, caveat in cast(dict[str, Any], merged.get("run_caveats") or {}).items()}
    run_caveats["run-02"] = RUN02_EXPLORATORY_CAVEAT
    merged["run_caveats"] = run_caveats
    merged["secondary_viewer_source"] = viewer_root.relative_to(repo_root).as_posix()
    merged["run_02_status"] = run02_status(repo_root, viewer_root)
    return merged


def annotate_run02_detail(detail: dict[str, Any], repo_root: Path) -> dict[str, Any]:
    detail["run_label"] = "Music (exploratory)"
    detail["run_caveat"] = RUN02_EXPLORATORY_CAVEAT
    detail["viewer_source"] = run02_viewer_root(repo_root).relative_to(repo_root).as_posix()
    detail["run_02_status"] = run02_status(repo_root, run02_viewer_root(repo_root))
    return detail


def load_dashboard_empirical_detail(repo_root: Path, subject: str, run: str) -> dict[str, Any] | None:
    viewer_root = repo_root / "results" / "stage_2" / "empirical_viewer"
    detail = load_empirical_viewer_detail(viewer_root, subject=subject, run=run)
    if detail is None and run == "run-02":
        detail = load_empirical_viewer_detail(run02_viewer_root(repo_root), subject=subject, run=run)
    if detail is not None and run == "run-02":
        return annotate_run02_detail(detail, repo_root)
    return detail
