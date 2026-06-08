from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_VERSION = "thesis_upgrade_status.v1"
MINIMUM_PAIRED_MOTION_CONTROL_ROWS = 4
REQUIRED_MOTION_CONTROL_FEATURE_FAMILIES = ("fd", "dvars", "censoring")
REQUIRED_NEUROMAPS_MAP_FAMILIES = ("receptor", "myelin", "functional_gradient", "gene_expression")
ROCKET_MINIMUM_BALANCED_ACCURACY = 0.60
ROCKET_MINIMUM_ROC_AUC = 0.60
STRICT_REQUIREMENT_IDS = (
    "schaefer_yeo_high_resolution",
    "neuromaps_spatial_autocorrelation_nulls",
    "ds006072_external_validation",
    "motion_confound_control_result",
    "receptor_myelin_gradient_claim",
    "project_phase",
)
PACKAGE_REQUIREMENT_IDS = (
    "public_dashboard_static_snapshot",
    "reproducible_archive_publication",
)
READINESS_SNAPSHOT_SUMMARY_KEYS = (
    "strict_complete_gates",
    "strict_total_gates",
    "strict_missing_requirement_ids",
    "remaining_hard_requirements",
    "completion_status",
    "thesis_status",
)

def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw

def _readiness_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    raw_summary = payload.get("readiness_summary")
    summary = raw_summary if isinstance(raw_summary, dict) else {}

    def _rows(key: str, fields: Iterable[str]) -> list[dict[str, Any]]:
        raw_rows = payload.get(key)
        rows = raw_rows if isinstance(raw_rows, list) else []
        return [
            {field: row.get(field) for field in fields}
            for row in rows
            if isinstance(row, dict)
        ]

    gates = [
        row
        for row in _rows("gates", ("label", "status", "ready"))
        if row.get("label") != "Public dashboard"
    ]
    package_requirements = [
        row
        for row in _rows("package_readiness_requirements", ("requirement_id", "status", "complete"))
        if row.get("requirement_id") != "public_dashboard_static_snapshot"
    ]
    return {
        "schema_version": payload.get("schema_version"),
        "readiness_summary": {key: summary.get(key) for key in READINESS_SNAPSHOT_SUMMARY_KEYS},
        "gates": gates,
        "strict_completion_requirements": _rows(
            "strict_completion_requirements",
            ("requirement_id", "status", "complete"),
        ),
        "package_readiness_requirements": package_requirements,
    }

def _rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()

def _evidence_paths(repo_root: Path, *paths: Path) -> str:
    return "; ".join(_rel(path, repo_root) for path in paths)

def _status_is_implemented(status: str) -> bool:
    return status.startswith(("implemented", "validated", "passed", "complete"))

def _int_payload_value(payload: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(payload.get(key) or default)
    except (TypeError, ValueError):
        return default

def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

def _motion_feature_family_coverage(rows: Any) -> dict[str, bool]:
    coverage = {family: False for family in REQUIRED_MOTION_CONTROL_FEATURE_FAMILIES}
    if not isinstance(rows, list):
        return coverage
    for row in rows:
        if not isinstance(row, dict):
            continue
        feature = str(row.get("motion_feature") or "").lower()
        if "fd" in feature or "framewise_displacement" in feature:
            coverage["fd"] = True
        if "dvars" in feature:
            coverage["dvars"] = True
        if any(token in feature for token in ("motion_outlier", "outlier", "censor", "scrub", "non_steady_state")):
            coverage["censoring"] = True
    return coverage

def _external_scoring_lock_details_verified(payload: dict[str, Any]) -> bool:
    scoring_lock = payload.get("scoring_lock")
    if not isinstance(scoring_lock, dict):
        return False
    if scoring_lock.get("scoring_lock_verified") is not True:
        return False
    if scoring_lock.get("missing_or_mismatched") != []:
        return False
    checked_files = scoring_lock.get("checked_files")
    if not isinstance(checked_files, dict) or not checked_files:
        return False
    for checked_file in checked_files.values():
        if not isinstance(checked_file, dict):
            return False
        expected_sha = checked_file.get("expected_sha256")
        current_sha = checked_file.get("current_sha256")
        if (
            checked_file.get("exists") is not True
            or checked_file.get("verified") is not True
            or not isinstance(expected_sha, str)
            or not isinstance(current_sha, str)
            or not expected_sha
            or expected_sha != current_sha
        ):
            return False
    return True
