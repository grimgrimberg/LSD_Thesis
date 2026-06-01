from __future__ import annotations

import csv
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsd_thesis.data.ds003059 import _download_url_to_path
from lsd_thesis.ds006072_validation import (
    DS006072_DATASET_ID,
    MIN_COMPARABLE_SUBJECTS,
    classify_session,
    load_drug_order,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "ds006072_minimum_payload_plan.v1"
PRIMARY_CONDITIONS = ("active_control_mtp", "psilocybin")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _boolish(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _session_suffix(session_id: str, patient: str) -> str:
    prefix = f"{patient}_"
    if session_id.startswith(prefix):
        return session_id[len(prefix) :]
    if "_" in session_id:
        return session_id.split("_", 1)[1]
    return session_id


def _openneuro_subject_token(patient: str) -> str:
    if patient.startswith("P"):
        return f"sub-{patient[1:]}"
    return f"sub-{patient}"


def _matching_cifti_rows(
    *,
    cifti_rows: list[dict[str, str]],
    patient: str,
    session_suffix: str,
) -> list[dict[str, str]]:
    token = _openneuro_subject_token(patient)
    prefix = f"{token}_{session_suffix}_"
    return [
        row
        for row in cifti_rows
        if _boolish(row.get("is_processed_rest_cifti"))
        and _boolish(row.get("url_available"))
        and str(row.get("filename", "")).startswith(prefix)
    ]


def _local_file_status(data_root: Path, row: dict[str, str]) -> tuple[Path, bool, int, int | None]:
    expected_size = int(row.get("size") or 0)
    local_path = data_root / str(row.get("relative_path") or "")
    if not local_path.exists() or not local_path.is_file():
        return local_path, False, expected_size, None
    actual_size = int(local_path.stat().st_size)
    return local_path, expected_size <= 0 or actual_size == expected_size, expected_size, actual_size


def _condition_candidates(repo_root: Path) -> dict[str, dict[str, list[dict[str, Any]]]]:
    data_root = repo_root / "data" / DS006072_DATASET_ID
    session_rows = _read_csv(data_root / "session_data.csv")
    cifti_rows = _read_csv(data_root / "ds006072_cifti_manifest.csv")
    drug_order, _ = load_drug_order(repo_root)
    by_subject: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for session_row in session_rows:
        patient = str(session_row.get("PatientName") or "").strip()
        session_id = str(session_row.get("SessionID") or "").strip()
        if not patient or not session_id:
            continue
        condition = classify_session(session_id, patient, drug_order)
        if condition not in PRIMARY_CONDITIONS:
            continue
        suffix = _session_suffix(session_id, patient)
        matches = _matching_cifti_rows(cifti_rows=cifti_rows, patient=patient, session_suffix=suffix)
        for match in matches:
            local_path, local_ready, expected_size, actual_size = _local_file_status(data_root, match)
            by_subject.setdefault(patient, {}).setdefault(condition, []).append(
                {
                    "subject": patient,
                    "condition": condition,
                    "session_id": session_id,
                    "session_suffix": suffix,
                    "filename": str(match.get("filename") or ""),
                    "relative_path": str(match.get("relative_path") or ""),
                    "url": str(match.get("url") or ""),
                    "size_bytes": expected_size,
                    "local_path": _rel(local_path, repo_root),
                    "local_file_ready": local_ready,
                    "local_size_bytes": actual_size,
                }
            )
    return by_subject


def _choose_condition_file(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not rows:
        return None
    return sorted(rows, key=lambda row: (0 if row.get("local_file_ready") else 1, int(row.get("size_bytes") or 0), str(row.get("filename") or "")))[0]


def build_ds006072_payload_plan_status(
    repo_root: Path = REPO_ROOT,
    *,
    minimum_subjects: int = MIN_COMPARABLE_SUBJECTS,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    data_root = repo_root / "data" / DS006072_DATASET_ID
    by_subject = _condition_candidates(repo_root)
    comparable_subject_rows: list[dict[str, Any]] = []
    planned_files: list[dict[str, Any]] = []
    for subject in sorted(by_subject):
        condition_files = {
            condition: _choose_condition_file(by_subject[subject].get(condition, []))
            for condition in PRIMARY_CONDITIONS
        }
        if any(file_row is None for file_row in condition_files.values()):
            continue
        files: list[dict[str, Any]] = []
        for condition in PRIMARY_CONDITIONS:
            file_row = condition_files[condition]
            if file_row is not None:
                files.append(file_row)
        subject_ready = all(bool(file_row["local_file_ready"]) for file_row in files)
        comparable_subject_rows.append(
            {
                "subject": subject,
                "conditions": list(PRIMARY_CONDITIONS),
                "planned_file_count": len(files),
                "total_size_bytes": int(sum(int(file_row["size_bytes"]) for file_row in files)),
                "local_payload_ready": subject_ready,
            }
        )
        planned_files.extend(files)

    selected_subjects = comparable_subject_rows[: max(int(minimum_subjects), 0)]
    selected_subject_ids = {row["subject"] for row in selected_subjects}
    selected_files = [row for row in planned_files if row["subject"] in selected_subject_ids]
    selected_local_ready_subjects = [row for row in selected_subjects if row["local_payload_ready"]]
    selected_subject_count = len(selected_subjects)
    local_ready_subject_count = len(selected_local_ready_subjects)
    minimum_met_by_manifest = selected_subject_count >= minimum_subjects
    minimum_met_locally = local_ready_subject_count >= minimum_subjects
    if minimum_met_locally:
        analysis_status = "minimum_validation_payloads_local_ready_for_extraction"
        blocker = "Minimum paired ds006072 processed CIFTI payloads are local. Run the extraction writer, then unchanged scoring."
    elif minimum_met_by_manifest:
        analysis_status = "minimum_payload_download_plan_ready_missing_local_payloads"
        blocker = "Minimum paired processed CIFTI payloads are identified, but they are not downloaded locally."
    else:
        analysis_status = "blocked_insufficient_downloadable_primary_pairs"
        blocker = "The local ds006072 manifests do not identify enough downloadable paired psilocybin/MTP processed CIFTIs."

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "dataset_id": DS006072_DATASET_ID,
        "analysis_status": analysis_status,
        "minimum_subjects_required": int(minimum_subjects),
        "candidate_comparable_subject_count": len(comparable_subject_rows),
        "selected_subject_count": selected_subject_count,
        "selected_local_ready_subject_count": local_ready_subject_count,
        "selected_subjects": selected_subjects,
        "selected_files": selected_files,
        "selected_file_count": len(selected_files),
        "selected_total_size_bytes": int(sum(int(row["size_bytes"]) for row in selected_files)),
        "minimum_payload_plan_ready": minimum_met_by_manifest,
        "minimum_payloads_local_ready": minimum_met_locally,
        "data_root": _rel(data_root, repo_root),
        "blocker": blocker,
        "next_commands": [
            ".\\.venv\\Scripts\\python.exe scripts\\build_ds006072_payload_plan.py",
            ".\\.venv\\Scripts\\python.exe scripts\\build_ds006072_payload_plan.py --execute",
            ".\\.venv\\Scripts\\python.exe scripts\\build_ds006072_comparable_validation.py",
        ],
        "extraction_contract_after_download": [
            "Load each selected processed rest CIFTI from data/ds006072/NON_BIDS/ciftis/.",
            "Project to the same module/parcellation contract used by the locked ds003059 scorer.",
            "Write results/psilocybin_ds006072/empirical_viewer/subject_views/*.json using ses-PLCB for MTP and ses-LSD for psilocybin.",
            "Run the unchanged ds003059 dynamic-mechanism scoring code without retuning.",
        ],
        "claim_status": (
            "minimum_payloads_local_ready_not_yet_extracted"
            if minimum_met_locally
            else "minimum_download_plan_ready_not_validation"
            if minimum_met_by_manifest
            else "not_ready_for_external_validation"
        ),
        "claim_guardrail": (
            "This is a concrete acquisition bridge for external validation. It is not a psilocybin replication result until "
            "the selected payloads are local, empirical-viewer records are written, and unchanged scoring is applied."
        ),
    }


def download_selected_payloads(status: dict[str, Any], repo_root: Path = REPO_ROOT) -> list[dict[str, Any]]:
    repo_root = repo_root.resolve()
    downloaded: list[dict[str, Any]] = []
    for row in status.get("selected_files", []):
        if not isinstance(row, dict) or bool(row.get("local_file_ready")):
            continue
        url = str(row.get("url") or "")
        if not url:
            continue
        destination = repo_root / str(row["local_path"])
        expected_size = int(row.get("size_bytes") or 0)
        _download_url_to_path(url, destination, expected_size)
        downloaded.append(
            {
                "subject": row.get("subject"),
                "condition": row.get("condition"),
                "local_path": _rel(destination, repo_root),
                "size_bytes": int(destination.stat().st_size),
            }
        )
    return downloaded


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# ds006072 Minimum Payload Plan",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Required comparable subjects: `{status['minimum_subjects_required']}`",
        f"- Selected subjects: `{status['selected_subject_count']}`",
        f"- Local-ready selected subjects: `{status['selected_local_ready_subject_count']}`",
        f"- Selected files: `{status['selected_file_count']}`",
        f"- Selected bytes: `{status['selected_total_size_bytes']}`",
        "",
        "## Selected files",
        "",
        "| Subject | Condition | Session | File | Local ready | Bytes |",
        "| --- | --- | --- | --- | ---: | ---: |",
    ]
    for row in status["selected_files"]:
        lines.append(
            "| {subject} | {condition} | {session} | {filename} | {ready} | {size} |".format(
                subject=row["subject"],
                condition=row["condition"],
                session=row["session_suffix"],
                filename=row["filename"],
                ready=str(row["local_file_ready"]).lower(),
                size=row["size_bytes"],
            )
        )
    lines.extend(["", "## Next commands", ""])
    lines.extend(f"- `{command}`" for command in status["next_commands"])
    lines.extend(["", "## Blocker", "", status["blocker"], ""])
    return "\n".join(lines)


def write_ds006072_payload_plan_status(
    repo_root: Path = REPO_ROOT,
    output_dir: Path | None = None,
    *,
    minimum_subjects: int = MIN_COMPARABLE_SUBJECTS,
    execute: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "psilocybin_ds006072"
    output_dir.mkdir(parents=True, exist_ok=True)
    status = build_ds006072_payload_plan_status(repo_root, minimum_subjects=minimum_subjects)
    downloaded = download_selected_payloads(status, repo_root) if execute else []
    if execute:
        status = build_ds006072_payload_plan_status(repo_root, minimum_subjects=minimum_subjects)
    status["download_execute_requested"] = bool(execute)
    status["downloaded_files"] = downloaded
    status_path = output_dir / "minimum_payload_plan.json"
    report_path = output_dir / "minimum_payload_plan.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status
