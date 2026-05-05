from __future__ import annotations

import json
import math
import os
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any, cast

import nibabel as nib
import numpy as np
import yaml
from nilearn import datasets
from nilearn.maskers import NiftiLabelsMasker
from pydantic import BaseModel, ConfigDict
from scipy.stats import ttest_rel

from lsd_thesis.core import MODULE_NAMES
from lsd_thesis.metrics import compute_observable_summary

OPENNEURO_GRAPHQL_URL = "https://openneuro.org/crn/graphql"
DS003059_DATASET_ID = "ds003059"
DS003059_VERSION = "1.0.0"
DS003059_SESSIONS: tuple[str, ...] = ("ses-LSD", "ses-PLCB")
HARVARD_OXFORD_CORTICAL_FILENAME = "HarvardOxford-cort-maxprob-thr25-2mm.nii.gz"
HARVARD_OXFORD_SUBCORTICAL_FILENAME = "HarvardOxford-sub-maxprob-thr25-2mm.nii.gz"
MODULE_ATLAS_LABELS: dict[str, dict[str, tuple[int, ...]]] = {
    "visual": {"cortical": (22, 23, 24, 31, 32, 36, 39, 40, 47, 48), "subcortical": ()},
    "auditory": {"cortical": (9, 10, 42, 44, 45, 46), "subcortical": ()},
    "salience": {"cortical": (2, 28, 29, 41), "subcortical": ()},
    "default_mode": {"cortical": (21, 25, 30, 31), "subcortical": ()},
    "executive_frontoparietal": {"cortical": (3, 4, 5, 6, 18, 19, 20), "subcortical": ()},
    "limbic_affective": {"cortical": (8, 27, 33, 34, 35), "subcortical": (9, 10, 11, 19, 20, 21)},
    "thalamic_gateway": {"cortical": (), "subcortical": (4, 15)},
    "sensorimotor": {"cortical": (7, 17, 26, 42, 43), "subcortical": ()},
}


def atlas_module_label_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for module_name, label_spec in MODULE_ATLAS_LABELS.items():
        for atlas_name, labels in label_spec.items():
            for label in labels:
                rows.append({"module": module_name, "atlas": atlas_name, "label": int(label)})
    return rows


def atlas_label_overlaps() -> dict[str, dict[int, tuple[str, ...]]]:
    label_to_modules: dict[str, dict[int, list[str]]] = {"cortical": {}, "subcortical": {}}
    for module_name, label_spec in MODULE_ATLAS_LABELS.items():
        for atlas_name, labels in label_spec.items():
            for label in labels:
                label_to_modules[atlas_name].setdefault(int(label), []).append(module_name)

    return {
        atlas_name: {
            label: tuple(module_names)
            for label, module_names in sorted(label_map.items())
            if len(module_names) > 1
        }
        for atlas_name, label_map in label_to_modules.items()
        if any(len(module_names) > 1 for module_names in label_map.values())
    }


def atlas_label_overlap_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for atlas_name, overlap_map in atlas_label_overlaps().items():
        for label, module_names in overlap_map.items():
            rows.append({"atlas": atlas_name, "label": label, "modules": list(module_names)})
    return rows


def _nilearn_data_roots(nilearn_data_dir: str | Path | None = None) -> tuple[Path, ...]:
    roots: list[Path] = []
    if nilearn_data_dir is not None:
        roots.append(Path(nilearn_data_dir))
    env_data = os.environ.get("NILEARN_DATA")
    if env_data:
        roots.extend(Path(item) for item in env_data.split(os.pathsep) if item)
    roots.append(Path.home() / "nilearn_data")
    deduped: list[Path] = []
    for root in roots:
        resolved = root.expanduser()
        if resolved not in deduped:
            deduped.append(resolved)
    return tuple(deduped)


def _load_cached_harvard_oxford_images(
    nilearn_data_dir: str | Path | None = None,
) -> tuple[nib.Nifti1Image, nib.Nifti1Image] | None:
    for root in _nilearn_data_roots(nilearn_data_dir):
        atlas_root = root / "fsl" / "data" / "atlases" / "HarvardOxford"
        cortical_path = atlas_root / HARVARD_OXFORD_CORTICAL_FILENAME
        subcortical_path = atlas_root / HARVARD_OXFORD_SUBCORTICAL_FILENAME
        if cortical_path.exists() and subcortical_path.exists():
            return cast(nib.Nifti1Image, nib.load(cortical_path)), cast(
                nib.Nifti1Image, nib.load(subcortical_path)
            )
    return None


def build_atlas_mapping_audit(
    labels_img: nib.Nifti1Image | None = None,
    include_voxel_counts: bool = True,
    nilearn_data_dir: str | Path | None = None,
    allow_fetch: bool = False,
) -> dict[str, Any]:
    module_voxel_counts: dict[str, int] = {}
    assigned_voxels: int | None = None
    unassigned_voxels: int | None = None
    if include_voxel_counts:
        try:
            resolved_labels_img = labels_img or _build_macro_module_labels_image(
                nilearn_data_dir=nilearn_data_dir,
                allow_fetch=allow_fetch,
            )
            label_volume = np.asarray(resolved_labels_img.dataobj, dtype=int)
            module_voxel_counts = {
                module_name: int(np.sum(label_volume == module_index))
                for module_index, module_name in enumerate(MODULE_NAMES, start=1)
            }
            assigned_voxels = int(np.sum(label_volume > 0))
            unassigned_voxels = int(np.sum(label_volume == 0))
        except FileNotFoundError:
            module_voxel_counts = {}

    return {
        "mapping": atlas_module_label_rows(),
        "overlaps": atlas_label_overlap_rows(),
        "module_voxel_counts": module_voxel_counts,
        "assigned_voxels": assigned_voxels,
        "unassigned_voxels": unassigned_voxels,
        "notes": [
            "Voxel counts are after overlap resolution in MODULE_NAMES order.",
            "This Harvard-Oxford-derived 8-module mapping is a transparent proxy, not a canonical network atlas.",
            "Voxel counts are omitted when include_voxel_counts is false to keep cached Stage 2 reruns non-blocking.",
        ],
    }


class Ds003059RunRecord(BaseModel):
    subject: str
    session: str
    run: str
    filename: str
    relative_path: str
    url: str
    size: int


class Ds003059RestManifest(BaseModel):
    subjects: tuple[str, ...]
    runs: tuple[Ds003059RunRecord, ...]
    sidecars: tuple[str, ...]


class Ds003059EmpiricalRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    subject: str
    session: str
    run: str
    relative_path: str
    timepoints: int
    metrics: dict[str, float]
    fc_matrix: np.ndarray
    time_series_path: str


def _mean_metric_dict(metric_dicts: list[dict[str, float]]) -> dict[str, float]:
    metric_names = metric_dicts[0].keys()
    return {
        name: float(np.mean([item[name] for item in metric_dicts]))
        for name in metric_names
    }


def _confidence_from_pvalue(placebo_vals: list[float], lsd_vals: list[float]) -> str:
    if len(placebo_vals) < 2:
        return "weak"
    result = ttest_rel(placebo_vals, lsd_vals)

    if result.pvalue is None or math.isnan(result.pvalue):
        return "weak"
    if result.pvalue < 0.01:
        return "strong"
    if result.pvalue < 0.05:
        return "moderate"
    return "weak"


def build_empirical_target_payloads(
    records: list[dict[str, Any]],
    module_names: tuple[str, ...],
) -> tuple[dict[str, Any], dict[str, Any]]:
    grouped_metrics: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    grouped_fc: dict[tuple[str, str], list[np.ndarray]] = defaultdict(list)

    for record in records:
        key = (str(record["subject"]), str(record["session"]))
        grouped_metrics[key].append(dict(record["metrics"]))
        grouped_fc[key].append(np.asarray(record["fc_matrix"], dtype=float))

    session_metrics: dict[tuple[str, str], dict[str, float]] = {
        key: _mean_metric_dict(metric_dicts) for key, metric_dicts in grouped_metrics.items()
    }
    session_fc: dict[tuple[str, str], np.ndarray] = {
        key: np.mean(matrices, axis=0) for key, matrices in grouped_fc.items()
    }

    placebo_keys = sorted(key for key in session_metrics if key[1] == "ses-PLCB")
    placebo_metric_rows = [session_metrics[key] for key in placebo_keys]
    placebo_fc_rows = [session_fc[key] for key in placebo_keys]
    sober_metrics = _mean_metric_dict(placebo_metric_rows)
    sober_fc = np.mean(placebo_fc_rows, axis=0)

    paired_subjects = sorted(
        subject
        for subject, session in session_metrics
        if session == "ses-PLCB" and (subject, "ses-LSD") in session_metrics
    )
    delta_rows: list[dict[str, float]] = []
    for subject in paired_subjects:
        placebo = session_metrics[(subject, "ses-PLCB")]
        lsd = session_metrics[(subject, "ses-LSD")]
        delta_rows.append({name: lsd[name] - placebo[name] for name in placebo})

    delta_means = _mean_metric_dict(delta_rows)
    confidence = {}
    for name in delta_means:
        p_vals = [session_metrics[(sub, "ses-PLCB")][name] for sub in paired_subjects]
        l_vals = [session_metrics[(sub, "ses-LSD")][name] for sub in paired_subjects]
        confidence[name] = _confidence_from_pvalue(p_vals, l_vals)

    weight_map = {
        "within_network_stability": 1.5,
        "cross_network_communication": 1.5,
        "thalamic_coupling": 1.2,
    }
    sober_payload = {
        "dataset_anchor": f"OpenNeuro ds003059 placebo resting-state summary ({len(placebo_keys)} session averages)",
        "module_names": list(module_names),
        "metrics": {
            name: {
                "target": value,
                "weight": weight_map.get(name, 1.0),
                "confidence": confidence.get(name, "moderate"),
                "note": "Estimated from actual ds003059 placebo resting-state runs (statistical tests used for confidence).",
            }
            for name, value in sober_metrics.items()
        },
        "fc_matrix": np.asarray(sober_fc, dtype=float).tolist(),
        "notes": [
            "Derived from ds003059 resting-state runs only (run-01 and run-03).",
            "Placebo summaries are averaged within subject, then averaged across subjects.",
        ],
    }
    perturbation_payload = {
        "metadata": {
            "source_strategy": "actual_ds003059",
            "paired_subject_count": len(paired_subjects),
            "notes": [
                "Delta targets are paired LSD minus placebo subject averages from ds003059.",
                "Confidence labels are derived from formal paired t-tests (p < 0.01 strong, p < 0.05 moderate).",
            ],
        },
        "target_deltas": delta_means,
        "confidence": confidence,
    }
    return sober_payload, perturbation_payload


def _record_to_dict(record: dict[str, Any] | BaseModel) -> dict[str, Any]:
    if isinstance(record, BaseModel):
        return dict(record.model_dump())
    return dict(record)


def _metric_sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def build_empirical_data_quality_payload(
    records: list[dict[str, Any] | BaseModel],
    empirical_deltas: dict[str, float] | None = None,
    literature_deltas: dict[str, float] | None = None,
) -> dict[str, Any]:
    rows = [_record_to_dict(record) for record in records]
    subjects = sorted({str(row["subject"]) for row in rows})
    sessions = sorted({str(row["session"]) for row in rows})
    runs = sorted({str(row["run"]) for row in rows})
    subject_sessions: dict[str, set[str]] = {subject: set() for subject in subjects}
    subject_session_runs: dict[tuple[str, str], set[str]] = {}
    session_run_counts: dict[str, dict[str, int]] = {}
    for row in rows:
        subject = str(row["subject"])
        session = str(row["session"])
        run = str(row["run"])
        subject_sessions[subject].add(session)
        subject_session_runs.setdefault((subject, session), set()).add(run)
        session_run_counts.setdefault(session, {}).setdefault(run, 0)
        session_run_counts[session][run] += 1

    expected_sessions = set(DS003059_SESSIONS)
    expected_runs = {"run-01", "run-03"}
    paired_subjects = [
        subject for subject, subject_session_set in subject_sessions.items()
        if expected_sessions.issubset(subject_session_set)
    ]
    complete_subjects = [
        subject
        for subject in paired_subjects
        if all(
            expected_runs.issubset(subject_session_runs.get((subject, session), set()))
            for session in expected_sessions
        )
    ]
    timepoints = [int(row["timepoints"]) for row in rows if row.get("timepoints") is not None]

    sign_conflicts: list[dict[str, Any]] = []
    if empirical_deltas is not None and literature_deltas is not None:
        for metric_name in sorted(set(empirical_deltas).intersection(literature_deltas)):
            empirical_delta = float(empirical_deltas[metric_name])
            literature_delta = float(literature_deltas[metric_name])
            if (
                _metric_sign(empirical_delta) != 0
                and _metric_sign(literature_delta) != 0
                and _metric_sign(empirical_delta) != _metric_sign(literature_delta)
            ):
                sign_conflicts.append(
                    {
                        "metric": metric_name,
                        "empirical_delta": empirical_delta,
                        "literature_delta": literature_delta,
                    }
                )

    return {
        "record_count": len(rows),
        "subjects": subjects,
        "subject_count": len(subjects),
        "sessions": sessions,
        "runs": runs,
        "session_run_counts": session_run_counts,
        "paired_subjects": paired_subjects,
        "paired_subject_count": len(paired_subjects),
        "complete_subjects": complete_subjects,
        "complete_subject_count": len(complete_subjects),
        "timepoints": {
            "min": min(timepoints) if timepoints else None,
            "max": max(timepoints) if timepoints else None,
            "mean": float(np.mean(timepoints)) if timepoints else None,
        },
        "sign_conflicts": sign_conflicts,
        "notes": [
            "Completeness expects ses-LSD and ses-PLCB, each with run-01 and run-03.",
            "Sign conflicts compare current ds003059 deltas with the literature-style target file.",
        ],
    }


def build_rest_manifest_from_listing(
    root_listing: list[dict[str, Any]],
    tree_lookup: dict[str, list[dict[str, Any]]],
) -> Ds003059RestManifest:
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
                if "_run-02_" in filename:
                    continue
                if "_run-01_" not in filename and "_run-03_" not in filename:
                    continue

                run = "run-01" if "_run-01_" in filename else "run-03"
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
    with urllib.request.urlopen(request, timeout=60) as response:
        body: dict[str, Any] = json.load(response)
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
      key
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
    return list(body["data"]["snapshot"]["files"])


def fetch_ds003059_rest_manifest(subjects: tuple[str, ...] | None = None) -> Ds003059RestManifest:
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

    return build_rest_manifest_from_listing(selected_subject_entries, tree_lookup)


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

    temp_path.replace(destination)
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


def _build_macro_module_labels_image(
    nilearn_data_dir: str | Path | None = None,
    allow_fetch: bool = True,
) -> nib.Nifti1Image:
    cached_images = _load_cached_harvard_oxford_images(nilearn_data_dir)
    if cached_images is not None:
        cortical_img, subcortical_img = cached_images
    elif allow_fetch:
        fetch_kwargs = {"data_dir": str(nilearn_data_dir)} if nilearn_data_dir is not None else {}
        cortical = datasets.fetch_atlas_harvard_oxford("cort-maxprob-thr25-2mm", **fetch_kwargs)
        subcortical = datasets.fetch_atlas_harvard_oxford("sub-maxprob-thr25-2mm", **fetch_kwargs)

        def _as_nifti_image(image_or_path: Any) -> nib.Nifti1Image:
            if isinstance(image_or_path, nib.Nifti1Image):
                return image_or_path
            return cast(nib.Nifti1Image, nib.load(image_or_path))

        cortical_img = _as_nifti_image(cortical.maps)
        subcortical_img = _as_nifti_image(subcortical.maps)
    else:
        raise FileNotFoundError("Cached Harvard-Oxford atlas files were not found.")

    cortical_data = np.asarray(cortical_img.dataobj)
    subcortical_data = np.asarray(subcortical_img.dataobj)
    module_data = np.zeros(cortical_data.shape, dtype=np.int16)

    # Overlapping source labels are resolved by MODULE_NAMES order; the audit
    # helpers above expose those overlaps so the proxy mapping stays explicit.
    for index, module_name in enumerate(MODULE_NAMES, start=1):
        label_spec = MODULE_ATLAS_LABELS[module_name]
        mask = np.zeros(cortical_data.shape, dtype=bool)
        if label_spec["cortical"]:
            mask |= np.isin(cortical_data, label_spec["cortical"])
        if label_spec["subcortical"]:
            mask |= np.isin(subcortical_data, label_spec["subcortical"])
        module_data[mask] = index

    return nib.Nifti1Image(module_data, cortical_img.affine)


def _standardize_time_series(time_series: np.ndarray) -> np.ndarray:
    centered = time_series - np.mean(time_series, axis=0, keepdims=True)
    if time_series.shape[0] < 2:
        return cast(np.ndarray, centered.astype(float, copy=False))
    sample_std = np.std(time_series, axis=0, ddof=1, keepdims=True)
    safe_std = np.where(sample_std < 1e-8, 1.0, sample_std)
    return cast(np.ndarray, (centered / safe_std).astype(float, copy=False))


def _extract_module_time_series_manually(
    bold_image: nib.Nifti1Image,
    labels_img: nib.Nifti1Image,
) -> np.ndarray:
    volume = np.asarray(bold_image.dataobj, dtype=float)
    if volume.ndim != 4:
        raise ValueError("BOLD image must be 4D.")

    label_volume = np.asarray(labels_img.dataobj, dtype=int)
    if label_volume.shape != volume.shape[:3]:
        raise ValueError("Label image shape must match the first three BOLD dimensions.")

    module_count = int(label_volume.max())
    time_series = np.zeros((volume.shape[3], module_count), dtype=float)
    for label_index in range(1, module_count + 1):
        mask = label_volume == label_index
        if not np.any(mask):
            continue
        time_series[:, label_index - 1] = volume[mask].mean(axis=0)

    return _standardize_time_series(time_series)


def extract_module_time_series(run_path: str | Path, labels_img: nib.Nifti1Image | None = None) -> np.ndarray:
    resolved_labels = labels_img or _build_macro_module_labels_image()
    resolved_run_path = Path(run_path)
    for attempt in range(3):
        masker = NiftiLabelsMasker(
            labels_img=resolved_labels,
            standardize="zscore_sample",
        )
        try:
            bold_image = cast(nib.Nifti1Image, nib.load(str(resolved_run_path)))
            materialized_image = nib.Nifti1Image(
                np.asarray(bold_image.dataobj),
                bold_image.affine,
                bold_image.header.copy(),
            )
            return np.asarray(masker.fit_transform(materialized_image), dtype=float)
        except OSError:
            if attempt == 2:
                break
        except ValueError as error:
            if "File not found:" not in str(error) or attempt == 2:
                break
    bold_image = cast(nib.Nifti1Image, nib.load(str(resolved_run_path)))
    return _extract_module_time_series_manually(bold_image, resolved_labels)


def extract_empirical_run_records(
    manifest: Ds003059RestManifest,
    dataset_dir: str | Path,
    output_dir: str | Path,
) -> tuple[Ds003059EmpiricalRecord, ...]:
    labels_img = _build_macro_module_labels_image()
    dataset_root = Path(dataset_dir)
    output_root = Path(output_dir)
    series_root = output_root / "module_time_series"
    series_root.mkdir(parents=True, exist_ok=True)

    records: list[Ds003059EmpiricalRecord] = []
    for run in manifest.runs:
        run_path = dataset_root / run.relative_path
        time_series = extract_module_time_series(run_path, labels_img=labels_img)
        observable = compute_observable_summary(time_series, MODULE_NAMES)
        series_path = series_root / f"{run.subject}_{run.session}_{run.run}_modules.npy"
        np.save(series_path, time_series)
        # Store path relative to output_dir for portability
        relative_series_path = series_path.relative_to(output_root)
        records.append(
            Ds003059EmpiricalRecord(
                subject=run.subject,
                session=run.session,
                run=run.run,
                relative_path=run.relative_path,
                timepoints=int(time_series.shape[0]),
                metrics=observable.metric_map(),
                fc_matrix=observable.fc_matrix,
                time_series_path=str(relative_series_path),
            )
        )

    return tuple(records)


def _to_plain_python(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _to_plain_python(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain_python(item) for item in value]
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.integer):
        return int(value)
    return value


def generate_empirical_targets(
    dataset_dir: str | Path,
    output_dir: str | Path,
    subjects: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    sober_path = output_path / "empirical_sober_targets.yaml"
    perturbation_path = output_path / "empirical_perturbation_targets.yaml"
    manifest_path = output_path / "ds003059_rest_manifest.json"
    records_path = output_path / "empirical_run_summaries.json"

    if sober_path.exists() and perturbation_path.exists() and manifest_path.exists() and records_path.exists():
        manifest = Ds003059RestManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
        run_records = tuple(
            Ds003059EmpiricalRecord.model_validate(
                {
                    **record,
                    "fc_matrix": np.asarray(record["fc_matrix"], dtype=float),
                }
            )
            for record in json.loads(records_path.read_text(encoding="utf-8"))
        )
        return {
            "manifest": manifest,
            "run_records": run_records,
            "sober_target_path": str(sober_path),
            "perturbation_target_path": str(perturbation_path),
        }

    manifest = fetch_ds003059_rest_manifest(subjects=subjects)
    download_ds003059_rest_runs(manifest, target_dir=dataset_dir)
    run_records = extract_empirical_run_records(
        manifest=manifest,
        dataset_dir=dataset_dir,
        output_dir=output_dir,
    )
    serialized_records = [
        {
            "subject": record.subject,
            "session": record.session,
            "run": record.run,
            "relative_path": record.relative_path,
            "timepoints": record.timepoints,
            "metrics": record.metrics,
            "fc_matrix": record.fc_matrix,
            "time_series_path": record.time_series_path,
        }
        for record in run_records
    ]
    sober_payload, perturbation_payload = build_empirical_target_payloads(
        records=serialized_records,
        module_names=MODULE_NAMES,
    )

    sober_path.write_text(yaml.safe_dump(_to_plain_python(sober_payload), sort_keys=False), encoding="utf-8")
    perturbation_path.write_text(
        yaml.safe_dump(_to_plain_python(perturbation_payload), sort_keys=False),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(_to_plain_python(manifest.model_dump()), indent=2), encoding="utf-8")
    records_path.write_text(json.dumps(_to_plain_python(serialized_records), indent=2), encoding="utf-8")

    return {
        "manifest": manifest,
        "run_records": run_records,
        "sober_target_path": str(sober_path),
        "perturbation_target_path": str(perturbation_path),
    }
