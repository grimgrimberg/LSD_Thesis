from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from lsd_thesis.setting_seed.motion import MOTION_FILE_PATTERN, build_motion_summary, discover_motion_files

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "ds003059_motion_source_availability.v1"
OPENNEURO_GRAPHQL_URL = "https://openneuro.org/crn/graphql"
DS003059_DATASET_ID = "ds003059"
DS003059_VERSION = "1.0.0"
PUBLIC_DERIVATIVE_REPOS = (
    "https://github.com/OpenNeuroDerivatives/ds003059-fmriprep",
    "https://github.com/OpenNeuroDerivatives/ds003059-mriqc",
)


def _rel(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _is_motion_like(filename: str) -> bool:
    return bool(MOTION_FILE_PATTERN.search(filename)) or bool(
        re.search(r"(desc-confounds|framewise_displacement|std_dvars|dvars|motion_outlier)", filename, re.IGNORECASE)
    )


def query_openneuro_snapshot_files(
    dataset_id: str = DS003059_DATASET_ID,
    tag: str = DS003059_VERSION,
    endpoint: str = OPENNEURO_GRAPHQL_URL,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    query = (
        "query MotionFiles($datasetId: ID!, $tag: String!) { "
        "snapshot(datasetId: $datasetId, tag: $tag) { "
        "files(recursive: true) { filename directory size annexed } "
        "} }"
    )
    body = json.dumps({"query": query, "variables": {"datasetId": dataset_id, "tag": tag}}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json", "User-Agent": "lsd-thesis-motion-source-check"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if payload.get("errors"):
        raise RuntimeError(json.dumps(payload["errors"]))
    files = payload.get("data", {}).get("snapshot", {}).get("files", [])
    if not isinstance(files, list):
        return []
    return [item for item in files if isinstance(item, dict)]


def query_url_status(url: str, timeout: float = 15.0) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": "lsd-thesis-motion-source-check"}, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return {"url": url, "status_code": int(response.status), "available": 200 <= int(response.status) < 400}
    except urllib.error.HTTPError as error:
        return {"url": url, "status_code": int(error.code), "available": False}
    except Exception as error:
        return {"url": url, "status_code": None, "available": False, "error": str(error)}


def build_motion_source_availability(
    repo_root: str | Path = REPO_ROOT,
    *,
    roots: Sequence[str | Path] | None = None,
    openneuro_files: Sequence[dict[str, Any]] | None = None,
    derivative_repo_statuses: Sequence[dict[str, Any]] | None = None,
    fetch_remote: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    motion_roots = tuple(Path(item) for item in roots) if roots is not None else None
    local_files = discover_motion_files(repo_root=root, roots=motion_roots)
    local_summary = build_motion_summary(repo_root=root, roots=motion_roots)
    remote_error: str | None = None
    if openneuro_files is None and fetch_remote:
        try:
            openneuro_files = query_openneuro_snapshot_files()
        except Exception as error:
            openneuro_files = []
            remote_error = str(error)
    if derivative_repo_statuses is None and fetch_remote:
        derivative_repo_statuses = [query_url_status(url) for url in PUBLIC_DERIVATIVE_REPOS]

    openneuro_files = tuple(openneuro_files or ())
    derivative_repo_statuses = tuple(derivative_repo_statuses or ())
    openneuro_motion_like = [
        item
        for item in openneuro_files
        if _is_motion_like(str(item.get("filename") or "")) and not bool(item.get("directory"))
    ]
    derivative_available = any(bool(item.get("available")) for item in derivative_repo_statuses)
    local_available = bool(local_summary.get("motion_analysis_ready"))
    raw_snapshot_checked = bool(openneuro_files) or remote_error is not None
    raw_snapshot_has_confounds = bool(openneuro_motion_like)
    source_confounds_available = local_available or raw_snapshot_has_confounds or derivative_available
    analysis_status = (
        "authorized_subject_level_motion_confounds_available"
        if source_confounds_available
        else "no_authorized_subject_level_motion_confounds_found"
        if raw_snapshot_checked and derivative_repo_statuses
        else "local_motion_confounds_not_found_remote_not_checked"
    )
    conclusion = (
        "Subject-level FD/DVARS/censoring inputs are available from at least one checked source."
        if source_confounds_available
        else (
            "Local repo search, OpenNeuro ds003059 snapshot metadata, and public "
            "OpenNeuroDerivatives repo checks did not expose subject-level "
            "FD/DVARS/censoring confounds."
        )
        if raw_snapshot_checked and derivative_repo_statuses
        else (
            "Local repo search found no subject-level FD/DVARS/censoring confounds; "
            "remote source checks have not been executed."
        )
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "analysis_status": analysis_status,
        "motion_source_availability_ready": True,
        "dataset": {"id": DS003059_DATASET_ID, "version": DS003059_VERSION},
        "local_search": {
            "motion_file_count": len(local_files),
            "motion_files": [_rel(path, root) for path in local_files],
            "configured_motion_roots": [_rel(path, root) for path in motion_roots] if motion_roots else [],
            "motion_like_files_present": bool(local_files),
            "parseable_confounds_available": local_available,
            "motion_summary_status": local_summary.get("status"),
            "motion_analysis_ready": bool(local_summary.get("motion_analysis_ready")),
            "motion_pairing_ready": bool(local_summary.get("motion_pairing_ready")),
            "parsed_summary_count": int(local_summary.get("parsed_summary_count") or 0),
            "unusable_file_count": int(local_summary.get("unusable_file_count") or 0),
            "paired_subject_run_count": int(local_summary.get("paired_subject_run_count") or 0),
            "minimum_paired_subject_run_count": int(local_summary.get("minimum_paired_subject_run_count") or 0),
        },
        "openneuro_raw_snapshot": {
            "checked": raw_snapshot_checked,
            "file_count": len(openneuro_files),
            "confound_like_file_count": len(openneuro_motion_like),
            "confound_like_files": [str(item.get("filename") or "") for item in openneuro_motion_like[:50]],
            "error": remote_error,
            "query": "snapshot.files(recursive=true)",
            "dataset_type_note": "ds003059 declares DatasetType=derivative locally; snapshot file presence is not original-raw-BIDS proof.",
        },
        "public_derivative_repositories": {
            "checked": bool(derivative_repo_statuses),
            "statuses": list(derivative_repo_statuses),
            "available_count": sum(1 for item in derivative_repo_statuses if item.get("available")),
        },
        "source_confounds_available": source_confounds_available,
        "conclusion": conclusion,
        "next_action": (
            "Ingest the available confound files with scripts/run_setting_seed_motion_summary.py, "
            "then rerun scripts/build_motion_confound_controls.py."
            if source_confounds_available
            else (
                "Supply authorized fMRIPrep desc-confounds_timeseries.tsv files or run "
                "fMRIPrep/MRIQC from ds003059 raw BOLD before claiming full subject-level "
                "motion control."
            )
        ),
        "claim_guardrail": (
            "This artifact proves source availability, not motion safety. Local motion-like files "
            "count as available only after they parse with joinable subject/session/run metadata; "
            "the motion-control gate can only pass after real subject/run FD, DVARS, and censoring "
            "values join to dynamic deltas."
        ),
    }


def write_motion_source_availability(
    repo_root: str | Path = REPO_ROOT,
    output_dir: str | Path | None = None,
    *,
    roots: Sequence[str | Path] | None = None,
    fetch_remote: bool = False,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    out_dir = root / "results" / "confound_controls" if output_dir is None else Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = build_motion_source_availability(root, roots=roots, fetch_remote=fetch_remote)
    path = out_dir / "ds003059_motion_source_availability.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    payload["source_path"] = _rel(path, root)
    return payload
