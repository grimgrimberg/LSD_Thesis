from __future__ import annotations

import csv
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsd_thesis.data.ds003059 import _download_url_to_path, _run_graphql_query, query_snapshot_files

DS006072_DATASET_ID = "ds006072"
DEFAULT_METADATA_FILES = (
    "dataset_description.json",
    "README",
    "CHANGES",
    "LICENSE",
    "session_data.csv",
    "PPFM_session_notes jss 20250402.xlsx",
)
FUNC_MANIFEST_FILENAME = "ds006072_func_manifest.json"
FUNC_MANIFEST_CSV_FILENAME = "ds006072_func_manifest.csv"
CIFTI_MANIFEST_CSV_FILENAME = "ds006072_cifti_manifest.csv"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def fetch_ds006072_latest_tag() -> str:
    query = f"""
query {{
  dataset(id: "{DS006072_DATASET_ID}") {{
    latestSnapshot {{
      tag
    }}
  }}
}}
""".strip()
    body = _run_graphql_query(query)
    tag = body["data"]["dataset"]["latestSnapshot"]["tag"]
    return str(tag)


def fetch_ds006072_root_listing(tag: str | None = None) -> list[dict[str, Any]]:
    resolved_tag = tag or fetch_ds006072_latest_tag()
    return query_snapshot_files(DS006072_DATASET_ID, resolved_tag)


def _query_children(tag: str, entry: dict[str, Any]) -> list[dict[str, Any]]:
    return query_snapshot_files(DS006072_DATASET_ID, tag, tree=str(entry["key"]))


def _session_lookup(target_dir: Path) -> dict[str, dict[str, str]]:
    session_path = target_dir / "session_data.csv"
    if not session_path.exists():
        return {}
    rows = list(csv.DictReader(session_path.open("r", encoding="utf-8", newline="")))
    lookup: dict[str, dict[str, str]] = {}
    for row in rows:
        session_number = str(row.get("SessionNumber", ""))
        if session_number:
            lookup[session_number] = {str(key): str(value) for key, value in row.items()}
    return lookup


def _classify_session(session_row: dict[str, str] | None) -> str:
    if not session_row:
        return "unknown"
    session_id = str(session_row.get("SessionID", "")).lower()
    if "baseline" in session_id or "nondrug" in session_id:
        return "baseline_nondrug"
    if "drug" in session_id:
        return "drug_session_requires_order_mapping"
    if "between" in session_id:
        return "between_drug_followup"
    if "after" in session_id:
        return "post_drug_followup"
    return "unknown"


def _parse_func_filename(filename: str) -> dict[str, Any]:
    run_match = re.search(r"_run-([A-Za-z0-9]+)", filename)
    echo_match = re.search(r"_echo-([A-Za-z0-9]+)", filename)
    task_match = re.search(r"_task-([A-Za-z0-9]+)", filename)
    suffix = filename.rsplit("_", 1)[-1] if "_" in filename else filename
    task = task_match.group(1) if task_match else ""
    task_key = task.lower()
    return {
        "task": task,
        "run": f"run-{run_match.group(1)}" if run_match else "",
        "echo": f"echo-{echo_match.group(1)}" if echo_match else "",
        "suffix": suffix,
        "is_rest": "_task-rest" in filename or task_key.startswith("boldrest"),
        "is_bold_nifti": filename.endswith("_bold.nii.gz") or filename.endswith("_bold.nii"),
        "is_bold_json": filename.endswith("_bold.json"),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers = sorted({key for row in rows for key in row})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def build_ds006072_func_manifest(
    target_dir: str | Path,
    *,
    tag: str | None = None,
) -> dict[str, Any]:
    resolved_tag = tag or fetch_ds006072_latest_tag()
    target_root = Path(target_dir)
    target_root.mkdir(parents=True, exist_ok=True)
    session_rows = _session_lookup(target_root)
    manifest_path = target_root / FUNC_MANIFEST_FILENAME
    existing_manifest = (
        json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest_path.exists()
        else None
    )
    root_listing = fetch_ds006072_root_listing(resolved_tag)
    subject_entries = [
        entry
        for entry in root_listing
        if entry.get("directory") and str(entry.get("filename", "")).startswith("sub-")
    ]
    if isinstance(existing_manifest, dict) and existing_manifest.get("snapshot_tag") == resolved_tag and existing_manifest.get("rows"):
        file_rows = list(existing_manifest["rows"])
    else:
        file_rows = []
        for subject_entry in subject_entries:
            subject = str(subject_entry["filename"])
            for session_entry in _query_children(resolved_tag, subject_entry):
                if not session_entry.get("directory"):
                    continue
                session = str(session_entry["filename"])
                if not session.startswith("ses-"):
                    continue
                session_key = f"{subject}_{session}"
                session_row = session_rows.get(session_key)
                for child in _query_children(resolved_tag, session_entry):
                    if not child.get("directory") or str(child.get("filename")) != "func":
                        continue
                    for file_entry in _query_children(resolved_tag, child):
                        if file_entry.get("directory"):
                            continue
                        filename = str(file_entry.get("filename", ""))
                        parsed = _parse_func_filename(filename)
                        relative_path = f"{subject}/{session}/func/{filename}"
                        urls = file_entry.get("urls") or []
                        file_rows.append(
                            {
                                "subject": subject,
                                "session": session,
                                "session_key": session_key,
                                "session_id": session_row.get("SessionID", "") if session_row else "",
                                "session_class": _classify_session(session_row),
                                "filename": filename,
                                "relative_path": relative_path,
                                "size": int(file_entry.get("size", 0)),
                                "url_available": bool(urls),
                                "url": str(urls[0]) if urls else "",
                                **parsed,
                            }
                        )

    rest_bold_rows = [row for row in file_rows if row["is_rest"] and row["is_bold_nifti"]]
    cifti_rows: list[dict[str, Any]] = []
    non_bids_entry = next((entry for entry in root_listing if entry.get("directory") and entry.get("filename") == "NON_BIDS"), None)
    if non_bids_entry is not None:
        non_bids_children = _query_children(resolved_tag, non_bids_entry)
        ciftis_entry = next((entry for entry in non_bids_children if entry.get("directory") and entry.get("filename") == "ciftis"), None)
        if ciftis_entry is not None:
            for entry in _query_children(resolved_tag, ciftis_entry):
                if entry.get("directory"):
                    continue
                filename = str(entry.get("filename", ""))
                urls = entry.get("urls") or []
                cifti_rows.append(
                    {
                        "filename": filename,
                        "relative_path": f"NON_BIDS/ciftis/{filename}",
                        "size": int(entry.get("size", 0)),
                        "url_available": bool(urls),
                        "url": str(urls[0]) if urls else "",
                        "is_processed_rest_cifti": filename.endswith(".dtseries.nii") and "rsfMRI" in filename,
                        "is_atlas_cifti": filename.endswith(".dtseries.nii") and "upck_faln" in filename,
                    }
                )
    manifest = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "dataset_id": DS006072_DATASET_ID,
        "snapshot_tag": resolved_tag,
        "target_dir": target_root.resolve().as_posix(),
        "subject_count": len(subject_entries),
        "functional_file_count": len(file_rows),
        "rest_bold_nifti_count": len(rest_bold_rows),
        "rest_bold_total_size_bytes": int(sum(int(row["size"]) for row in rest_bold_rows)),
        "processed_cifti_count": len(cifti_rows),
        "processed_rest_cifti_count": len([row for row in cifti_rows if row["is_processed_rest_cifti"]]),
        "processed_cifti_total_size_bytes": int(sum(int(row["size"]) for row in cifti_rows)),
        "session_classes": sorted({str(row["session_class"]) for row in file_rows}),
        "rows": file_rows,
        "cifti_rows": cifti_rows,
        "guardrail": (
            "This manifest identifies candidate ds006072 functional files for ingestion. It does not prove that "
            "the files are comparable to ds003059 until condition mapping, preprocessing choice, and extraction are implemented."
        ),
    }
    csv_path = target_root / FUNC_MANIFEST_CSV_FILENAME
    cifti_csv_path = target_root / CIFTI_MANIFEST_CSV_FILENAME
    manifest["source_path"] = manifest_path.as_posix()
    manifest["csv_path"] = csv_path.as_posix()
    manifest["cifti_csv_path"] = cifti_csv_path.as_posix()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    _write_csv(csv_path, file_rows)
    _write_csv(cifti_csv_path, cifti_rows)
    return manifest


def download_ds006072_metadata(
    target_dir: str | Path,
    *,
    tag: str | None = None,
    filenames: tuple[str, ...] = DEFAULT_METADATA_FILES,
) -> dict[str, Any]:
    resolved_tag = tag or fetch_ds006072_latest_tag()
    target_root = Path(target_dir)
    target_root.mkdir(parents=True, exist_ok=True)
    wanted = set(filenames)
    root_listing = fetch_ds006072_root_listing(resolved_tag)
    downloaded: list[dict[str, Any]] = []
    missing = set(wanted)
    for entry in root_listing:
        filename = str(entry.get("filename", ""))
        if entry.get("directory") or filename not in wanted:
            continue
        urls = entry.get("urls") or []
        if not urls:
            continue
        destination = target_root / filename
        _download_url_to_path(str(urls[0]), destination, int(entry.get("size", 0)))
        downloaded.append(
            {
                "filename": filename,
                "path": destination.as_posix(),
                "size": int(entry.get("size", 0)),
            }
        )
        missing.discard(filename)

    manifest = {
        "schema_version": 1,
        "generated_at_utc": _now(),
        "dataset_id": DS006072_DATASET_ID,
        "snapshot_tag": resolved_tag,
        "target_dir": target_root.resolve().as_posix(),
        "downloaded": downloaded,
        "missing_requested_files": sorted(missing),
        "guardrail": (
            "This is a metadata/provenance slice only. It is not a completed psilocybin empirical viewer or imaging extraction."
        ),
    }
    manifest_path = target_root / "ds006072_metadata_manifest.json"
    manifest["source_path"] = manifest_path.as_posix()
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
