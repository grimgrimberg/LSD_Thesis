from __future__ import annotations

import json
import re
import shutil
import urllib.error
import urllib.request
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .constants import DS003059_DATASET_ID, DS003059_SESSIONS, DS003059_VERSION, OPENNEURO_GRAPHQL_URL
from .models import Ds003059RestManifest, Ds003059RunRecord
from .runs import normalize_ds003059_runs


def build_rest_manifest_from_listing(
    root_listing: list[dict[str, Any]],
    tree_lookup: dict[str, list[dict[str, Any]]],
    runs: Sequence[str] | None = None,
    *,
    include_music: bool = False,
) -> Ds003059RestManifest:
    selected_runs = set(normalize_ds003059_runs(runs, include_music=include_music))
    run_records: list[Ds003059RunRecord] = []
    sidecars: set[str] = set()
    subject_names: set[str] = set()

    for subject_entry in root_listing:
        if not subject_entry.get("directory", False):
            continue

        subject = str(subject_entry["filename"])
        if not subject.startswith("sub-"):
            continue

        for session_entry in tree_lookup.get(str(subject_entry["key"]), []):
            if not session_entry.get("directory", False):
                continue

            session = str(session_entry["filename"])
            if session not in {"ses-LSD", "ses-PLCB"}:
                continue

            func_entries = [
                item
                for item in tree_lookup.get(str(session_entry["key"]), [])
                if item.get("directory", False) and item.get("filename") == "func"
            ]
            if not func_entries:
                continue

            for file_entry in tree_lookup.get(str(func_entries[0]["key"]), []):
                filename = str(file_entry["filename"])
                if filename.startswith("._"):
                    continue

                relative_path = f"{subject}/{session}/func/{filename}"
                if filename.endswith("_task-rest_bold.json"):
                    sidecars.add(relative_path)
                    continue

                if not filename.endswith(".nii.gz"):
                    continue
                if "_task-rest_" not in filename:
                    continue
                run_match = re.search(r"_run-(\d+)_", filename)
                if run_match is None:
                    continue
                run = f"run-{run_match.group(1)}"
                if run not in selected_runs:
                    continue

                urls = file_entry.get("urls") or []
                run_records.append(
                    Ds003059RunRecord(
                        subject=subject,
                        session=session,
                        run=run,
                        filename=filename,
                        relative_path=relative_path,
                        url=str(urls[0]) if urls else "",
                        size=int(file_entry.get("size", 0)),
                    )
                )
                subject_names.add(subject)

    run_records.sort(key=lambda item: (item.subject, item.session, item.run))
    return Ds003059RestManifest(
        subjects=tuple(sorted(subject_names)),
        runs=tuple(run_records),
        sidecars=tuple(sorted(sidecars)),
    )

def _run_graphql_query(query: str) -> dict[str, Any]:
    payload = json.dumps({"query": query}).encode("utf-8")
    request = urllib.request.Request(
        OPENNEURO_GRAPHQL_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body: dict[str, Any] = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"OpenNeuro GraphQL HTTP error {exc.code} {exc.reason}: {detail}"
        ) from exc
    if "errors" in body:
        raise RuntimeError(f"OpenNeuro GraphQL query failed: {body['errors']}")
    return body

def query_snapshot_files(dataset_id: str, tag: str, tree: str | None = None) -> list[dict[str, Any]]:
    tree_argument = f'(tree: "{tree}")' if tree is not None else ""
    query = f"""
query {{
  snapshot(datasetId: "{dataset_id}", tag: "{tag}") {{
    files{tree_argument} {{
      filename
      id
      directory
      size
      annexed
      urls
    }}
  }}
}}
""".strip()
    body = _run_graphql_query(query)
    files = list(body["data"]["snapshot"]["files"])
    for file_entry in files:
        file_entry.setdefault("key", file_entry.get("id", ""))
    return files

def fetch_ds003059_rest_manifest(
    subjects: tuple[str, ...] | None = None,
    runs: Sequence[str] | None = None,
    *,
    include_music: bool = False,
) -> Ds003059RestManifest:
    root_listing = query_snapshot_files(DS003059_DATASET_ID, DS003059_VERSION)
    selected_subject_entries = [
        item
        for item in root_listing
        if item.get("directory", False)
        and str(item["filename"]).startswith("sub-")
        and (subjects is None or str(item["filename"]) in subjects)
    ]

    tree_lookup: dict[str, list[dict[str, Any]]] = {}
    for subject_entry in selected_subject_entries:
        subject_children = query_snapshot_files(
            DS003059_DATASET_ID,
            DS003059_VERSION,
            tree=str(subject_entry["key"]),
        )
        tree_lookup[str(subject_entry["key"])] = subject_children

        for session_entry in subject_children:
            if not session_entry.get("directory", False):
                continue
            if str(session_entry["filename"]) not in DS003059_SESSIONS:
                continue

            session_children = query_snapshot_files(
                DS003059_DATASET_ID,
                DS003059_VERSION,
                tree=str(session_entry["key"]),
            )
            tree_lookup[str(session_entry["key"])] = session_children

            for func_entry in session_children:
                if not func_entry.get("directory", False):
                    continue
                if func_entry.get("filename") != "func":
                    continue
                tree_lookup[str(func_entry["key"])] = query_snapshot_files(
                    DS003059_DATASET_ID,
                    DS003059_VERSION,
                    tree=str(func_entry["key"]),
                )

    return build_rest_manifest_from_listing(selected_subject_entries, tree_lookup, runs=runs, include_music=include_music)

def _download_url_to_path(url: str, destination: Path, expected_size: int) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and destination.stat().st_size == expected_size:
        return destination

    temp_path = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, temp_path.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)

    actual_size = temp_path.stat().st_size
    if expected_size > 0 and actual_size != expected_size:
        temp_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Download size mismatch for {destination}: expected {expected_size}, got {actual_size}."
        )

    try:
        temp_path.replace(destination)
    except PermissionError:
        shutil.copyfile(temp_path, destination)
    return destination

def download_ds003059_rest_runs(
    manifest: Ds003059RestManifest,
    target_dir: str | Path,
) -> tuple[Path, ...]:
    target_root = Path(target_dir)
    downloaded_paths: list[Path] = []
    for run in manifest.runs:
        destination = target_root / run.relative_path
        downloaded_paths.append(_download_url_to_path(run.url, destination, run.size))
    return tuple(downloaded_paths)
