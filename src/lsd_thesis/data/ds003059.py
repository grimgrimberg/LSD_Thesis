from __future__ import annotations

import json
import math
import os
import re
import shutil
import urllib.error
import urllib.request
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256
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
DS003059_DEFAULT_RUNS: tuple[str, ...] = ("run-01", "run-03")
DS003059_MUSIC_RUN = "run-02"
DS003059_MUSIC_RUNS: tuple[str, ...] = ("run-01", "run-02", "run-03")
DS003059_ALLOWED_RUNS: tuple[str, ...] = DS003059_MUSIC_RUNS
EMPIRICAL_CACHE_SCHEMA_VERSION = 1
EMPIRICAL_CACHE_METADATA_FILENAME = "empirical_cache_metadata.json"
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


def normalize_ds003059_runs(
    runs: Sequence[str] | None = None,
    *,
    include_music: bool = False,
) -> tuple[str, ...]:
    """Return a deterministic ds003059 run tuple with run-02 guarded by an explicit flag."""
    selected = DS003059_MUSIC_RUNS if runs is None and include_music else (DS003059_DEFAULT_RUNS if runs is None else tuple(str(run) for run in runs))
    if not selected:
        raise ValueError("At least one ds003059 run must be selected.")
    invalid = sorted(set(selected).difference(DS003059_ALLOWED_RUNS))
    if invalid:
        raise ValueError(f"Unsupported ds003059 runs: {invalid}. Allowed runs: {list(DS003059_ALLOWED_RUNS)}.")
    if DS003059_MUSIC_RUN in selected and not include_music:
        raise ValueError("run-02 music extraction requires include_music=True / --include-music.")
    selected_set = set(selected)
    return tuple(run for run in DS003059_ALLOWED_RUNS if run in selected_set)


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
    roots.append(Path(__file__).resolve().parents[3] / "results" / "nilearn_data")
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
        except OSError:
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


def _stable_json_hash(payload: Any) -> str:
    return sha256(
        json.dumps(_to_plain_python(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_file_provenance(
    manifest: Ds003059RestManifest,
    dataset_dir: str | Path | None,
) -> tuple[dict[str, dict[str, int | str]], list[str]]:
    if dataset_dir is None:
        return {}, []

    root = Path(dataset_dir)
    fingerprints: dict[str, dict[str, int | str]] = {}
    missing: list[str] = []
    for run in manifest.runs:
        run_path = root / run.relative_path
        if not run_path.exists():
            missing.append(run.relative_path)
            continue
        try:
            run_size = run_path.stat().st_size
            fingerprints[run.relative_path] = {
                "size": run_size,
                "sha256": _file_sha256(run_path),
                "manifest_size": run.size,
            }
        except OSError:
            missing.append(run.relative_path)

    return fingerprints, missing


def _manifest_core_payload(manifest: Ds003059RestManifest) -> dict[str, Any]:
    return {
        "subjects": list(manifest.subjects),
        "runs": [
            {
                "subject": run.subject,
                "session": run.session,
                "run": run.run,
                "filename": run.filename,
                "relative_path": run.relative_path,
                "size": run.size,
            }
            for run in manifest.runs
        ],
        "sidecars": list(manifest.sidecars),
    }


def sanitize_rest_manifest_for_cache(manifest: Ds003059RestManifest) -> Ds003059RestManifest:
    return Ds003059RestManifest(
        subjects=manifest.subjects,
        runs=tuple(run.model_copy(update={"url": ""}) for run in manifest.runs),
        sidecars=manifest.sidecars,
    )


def build_preprocessing_qc_summary(
    records: Sequence[dict[str, Any] | BaseModel],
    *,
    manifest: Ds003059RestManifest | None = None,
    module_names: tuple[str, ...] = MODULE_NAMES,
    selected_runs: Sequence[str] | None = None,
    include_music: bool = False,
) -> dict[str, Any]:
    selected_run_tuple = normalize_ds003059_runs(selected_runs, include_music=include_music)
    rows = [_record_to_dict(record) for record in records]
    missing_values = 0
    nonfinite_values = 0
    zero_variance_record_count = 0
    timepoint_values: list[int] = []
    for row in rows:
        if row.get("timepoints") is not None:
            timepoint_values.append(int(row["timepoints"]))
        for metric_value in dict(row.get("metrics", {})).values():
            if metric_value is None:
                missing_values += 1
                continue
            if not math.isfinite(float(metric_value)):
                nonfinite_values += 1
        fc_matrix = row.get("fc_matrix")
        if fc_matrix is not None:
            fc = np.asarray(fc_matrix, dtype=float)
            nonfinite_values += int(np.size(fc) - np.count_nonzero(np.isfinite(fc)))
        if row.get("time_series_path") is None:
            missing_values += 1
        if row.get("timepoints") == 0:
            zero_variance_record_count += 1

    input_count = len(manifest.runs) if manifest is not None else len(rows)
    output_count = len(rows)
    warnings = []
    if output_count == 0:
        warnings.append("No empirical records were available for QC summary generation.")
    if nonfinite_values:
        warnings.append("Non-finite metric or FC values were detected in empirical records.")
    excluded_reasons = [
        "appledouble_sidecar",
        "non_rest_task",
        "wrong_session",
        "non_nifti_bold",
        "missing_func_directory",
    ]
    if DS003059_MUSIC_RUN not in selected_run_tuple:
        excluded_reasons.insert(2, "run_02_music")

    return {
        "input_run_count": input_count,
        "output_record_count": output_count,
        "excluded_count": max(0, input_count - output_count),
        "missing_values": missing_values,
        "nonfinite_values": nonfinite_values,
        "zero_timepoint_record_count": zero_variance_record_count,
        "timepoints": {
            "min": min(timepoint_values) if timepoint_values else None,
            "max": max(timepoint_values) if timepoint_values else None,
            "mean": float(np.mean(timepoint_values)) if timepoint_values else None,
        },
        "transformations_applied": [
            f"Filter to ses-LSD/ses-PLCB, task-rest, selected runs: {', '.join(selected_run_tuple)}.",
            "Extract Harvard-Oxford-derived macro-module means with NiftiLabelsMasker standardize=zscore_sample when available.",
            "Use manual ROI averaging plus sample z-scoring as a fallback extraction path.",
        ],
        "parcellation": {
            "parcellation_id": "harvard_oxford_8_module_proxy",
            "atlas_source": "Harvard-Oxford cortical/subcortical atlases via Nilearn/FSL.",
            "module_count": len(module_names),
            "module_names": list(module_names),
            "conflict_resolution_policy": "Overlapping atlas labels are assigned in MODULE_NAMES order.",
            "mapping_fingerprint": _stable_json_hash(atlas_module_label_rows()),
        },
        "exclusion_policy": {
            "kept_sessions": list(DS003059_SESSIONS),
            "kept_runs": list(selected_run_tuple),
            "excluded_reasons": excluded_reasons,
        },
        "warnings": warnings,
        "limitations": [
            "The repository consumes the ds003059 derivative BOLD files; it does not rerun full scanner-level preprocessing.",
            "No motion, FD/DVARS, confound-regression, or censoring summary is derived in this lightweight QC layer.",
            "The 8-module mapping is a transparent proxy, not a canonical functional parcellation.",
        ],
    }


def _empirical_cache_fingerprint_inputs(
    *,
    output_path: Path,
    manifest: Ds003059RestManifest,
    requested_subjects: tuple[str, ...] | None,
    selected_runs: Sequence[str] | None = None,
    include_music: bool = False,
    dataset_dir: str | Path | None = None,
) -> dict[str, Any]:
    selected_run_tuple = normalize_ds003059_runs(selected_runs, include_music=include_music)
    artifact_names = (
        "empirical_sober_targets.yaml",
        "empirical_perturbation_targets.yaml",
        "ds003059_rest_manifest.json",
        "empirical_run_summaries.json",
    )
    artifact_hashes = {
        artifact_name: _file_sha256(output_path / artifact_name)
        for artifact_name in artifact_names
        if (output_path / artifact_name).exists()
    }
    payload: dict[str, Any] = {
        "schema_version": EMPIRICAL_CACHE_SCHEMA_VERSION,
        "dataset_id": DS003059_DATASET_ID,
        "dataset_version": DS003059_VERSION,
        "requested_subjects": list(requested_subjects) if requested_subjects is not None else None,
        "cached_subjects": list(manifest.subjects),
        "module_names": list(MODULE_NAMES),
        "atlas_mapping_fingerprint": _stable_json_hash(atlas_module_label_rows()),
        "manifest_core_fingerprint": _stable_json_hash(_manifest_core_payload(manifest)),
        "artifact_hashes": artifact_hashes,
    }
    if dataset_dir is not None:
        run_file_hashes, run_file_missing = _run_file_provenance(manifest, dataset_dir)
        payload["run_file_hashes"] = run_file_hashes
        payload["run_file_missing"] = run_file_missing
        payload["run_file_hash_status"] = "available" if run_file_hashes else "unavailable"
    if selected_run_tuple != DS003059_DEFAULT_RUNS:
        payload["selected_runs"] = list(selected_run_tuple)
        payload["include_music"] = DS003059_MUSIC_RUN in selected_run_tuple
        payload["target_runs"] = list(DS003059_DEFAULT_RUNS)
    return payload


def build_empirical_cache_metadata(
    *,
    output_path: Path,
    manifest: Ds003059RestManifest,
    records: Sequence[dict[str, Any] | BaseModel],
    requested_subjects: tuple[str, ...] | None,
    selected_runs: Sequence[str] | None = None,
    include_music: bool = False,
    dataset_dir: str | Path | None = None,
) -> dict[str, Any]:
    fingerprint_inputs = _empirical_cache_fingerprint_inputs(
        output_path=output_path,
        manifest=manifest,
        requested_subjects=requested_subjects,
        selected_runs=selected_runs,
        include_music=include_music,
        dataset_dir=dataset_dir,
    )
    preprocessing_qc = build_preprocessing_qc_summary(
        records,
        manifest=manifest,
        selected_runs=selected_runs,
        include_music=include_music,
    )
    return {
        **fingerprint_inputs,
        "cache_fingerprint": _stable_json_hash(fingerprint_inputs),
        "created_at_utc": datetime.now(UTC).isoformat(),
        "preprocessing_qc": preprocessing_qc,
        "warnings": [],
        "limitations": [
            "The cache fingerprint includes generated target/cache artifacts and available raw run-file provenance.",
            "Git metadata is recorded by Stage 2 summaries when available; cache validation does not require a Git repository.",
        ],
    }


def validate_empirical_cache_metadata(
    output_path: Path,
    requested_subjects: tuple[str, ...] | None,
    selected_runs: Sequence[str] | None = None,
    include_music: bool = False,
    dataset_dir: str | Path | None = None,
) -> dict[str, Any]:
    metadata_path = output_path / EMPIRICAL_CACHE_METADATA_FILENAME
    if not metadata_path.exists():
        raise ValueError(
            f"Empirical cache metadata is missing: {metadata_path}. Regenerate the empirical targets."
        )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError(f"Empirical cache metadata must be a JSON object: {metadata_path}.")
    if metadata.get("schema_version") != EMPIRICAL_CACHE_SCHEMA_VERSION:
        raise ValueError(
            "Empirical cache metadata schema mismatch: "
            f"expected {EMPIRICAL_CACHE_SCHEMA_VERSION}, got {metadata.get('schema_version')}."
        )
    expected_requested = list(requested_subjects) if requested_subjects is not None else None
    if metadata.get("requested_subjects") != expected_requested:
        raise ValueError(
            "Empirical cache requested-subject mismatch: "
            f"metadata has {metadata.get('requested_subjects')}, requested {expected_requested}."
        )
    selected_run_tuple = normalize_ds003059_runs(selected_runs, include_music=include_music)
    if selected_run_tuple != DS003059_DEFAULT_RUNS and metadata.get("selected_runs") != list(selected_run_tuple):
        raise ValueError(
            "Empirical cache selected-run mismatch: "
            f"metadata has {metadata.get('selected_runs')}, requested {list(selected_run_tuple)}."
        )
    manifest_path = output_path / "ds003059_rest_manifest.json"
    manifest = Ds003059RestManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    current_inputs = _empirical_cache_fingerprint_inputs(
        output_path=output_path,
        manifest=manifest,
        requested_subjects=requested_subjects,
        selected_runs=selected_run_tuple,
        include_music=include_music,
        dataset_dir=dataset_dir,
    )
    current_fingerprint = _stable_json_hash(current_inputs)
    if metadata.get("cache_fingerprint") != current_fingerprint:
        raise ValueError("Empirical cache fingerprint mismatch; regenerate the empirical targets.")
    if dataset_dir is not None and metadata.get("run_file_hash_status") == "available":
        if metadata.get("run_file_hashes") != current_inputs.get("run_file_hashes"):
            raise ValueError("Empirical cache raw run-file fingerprints changed; regenerate the empirical targets.")
    return metadata


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
    target_runs: Sequence[str] = DS003059_DEFAULT_RUNS,
) -> tuple[dict[str, Any], dict[str, Any]]:
    target_run_set = set(target_runs)
    target_records = [record for record in records if str(record.get("run")) in target_run_set]
    if not target_records:
        raise ValueError(f"Cannot build empirical targets: no records matched target runs {sorted(target_run_set)}.")
    grouped_metrics: dict[tuple[str, str], list[dict[str, float]]] = defaultdict(list)
    grouped_fc: dict[tuple[str, str], list[np.ndarray]] = defaultdict(list)

    for record in target_records:
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
    if not placebo_metric_rows:
        raise ValueError("Cannot build sober targets: no ses-PLCB resting records were provided.")
    sober_metrics = _mean_metric_dict(placebo_metric_rows)
    sober_fc = np.mean(placebo_fc_rows, axis=0)

    paired_subjects = sorted(
        subject
        for subject, session in session_metrics
        if session == "ses-PLCB" and (subject, "ses-LSD") in session_metrics
    )
    if not paired_subjects:
        raise ValueError(
            "Cannot build perturbation targets: no subjects have both ses-PLCB and ses-LSD records."
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
            f"Derived from ds003059 resting-state target runs only ({', '.join(target_runs)}).",
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
    expected_runs: Sequence[str] | None = None,
    include_music: bool = False,
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
    expected_run_set = set(normalize_ds003059_runs(expected_runs, include_music=include_music))
    paired_subjects = [
        subject for subject, subject_session_set in subject_sessions.items()
        if expected_sessions.issubset(subject_session_set)
    ]
    complete_subjects = [
        subject
        for subject in paired_subjects
        if all(
            expected_run_set.issubset(subject_session_runs.get((subject, session), set()))
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
        "preprocessing_qc": build_preprocessing_qc_summary(rows, selected_runs=tuple(expected_run_set), include_music=include_music),
        "notes": [
            f"Completeness expects ses-LSD and ses-PLCB, each with {', '.join(sorted(expected_run_set))}.",
            "Sign conflicts compare current ds003059 deltas with the literature-style target file.",
        ],
    }


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


def _build_macro_module_labels_image(
    nilearn_data_dir: str | Path | None = None,
    allow_fetch: bool = True,
) -> nib.Nifti1Image:
    cached_images = _load_cached_harvard_oxford_images(nilearn_data_dir)
    if cached_images is not None:
        cortical_img, subcortical_img = cached_images
    elif allow_fetch:
        fetch_data_dir = Path(nilearn_data_dir) if nilearn_data_dir is not None else _nilearn_data_roots(None)[0]
        fetch_kwargs = {"data_dir": str(fetch_data_dir)}
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
                time_series_path=relative_series_path.as_posix(),
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
    runs: Sequence[str] | None = None,
    *,
    include_music: bool = False,
) -> dict[str, Any]:
    selected_runs = normalize_ds003059_runs(runs, include_music=include_music)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    sober_path = output_path / "empirical_sober_targets.yaml"
    perturbation_path = output_path / "empirical_perturbation_targets.yaml"
    manifest_path = output_path / "ds003059_rest_manifest.json"
    records_path = output_path / "empirical_run_summaries.json"
    cache_metadata_path = output_path / EMPIRICAL_CACHE_METADATA_FILENAME

    if sober_path.exists() and perturbation_path.exists() and manifest_path.exists() and records_path.exists():
        try:
            cache_metadata = validate_empirical_cache_metadata(
                output_path,
                requested_subjects=subjects,
                selected_runs=selected_runs,
                include_music=include_music,
                dataset_dir=dataset_dir,
            )
        except ValueError:
            cache_metadata = None
        else:
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
                "cache_metadata": cache_metadata,
            }

    manifest = fetch_ds003059_rest_manifest(subjects=subjects, runs=selected_runs, include_music=include_music)
    download_ds003059_rest_runs(manifest, target_dir=dataset_dir)
    cache_manifest = sanitize_rest_manifest_for_cache(manifest)
    run_records = extract_empirical_run_records(
        manifest=cache_manifest,
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
            "time_series_path": Path(record.time_series_path).as_posix(),
        }
        for record in run_records
    ]
    sober_payload, perturbation_payload = build_empirical_target_payloads(
        records=serialized_records,
        module_names=MODULE_NAMES,
        target_runs=DS003059_DEFAULT_RUNS,
    )

    sober_path.write_text(yaml.safe_dump(_to_plain_python(sober_payload), sort_keys=False), encoding="utf-8")
    perturbation_path.write_text(
        yaml.safe_dump(_to_plain_python(perturbation_payload), sort_keys=False),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(_to_plain_python(cache_manifest.model_dump()), indent=2), encoding="utf-8")
    records_path.write_text(json.dumps(_to_plain_python(serialized_records), indent=2), encoding="utf-8")
    cache_metadata = build_empirical_cache_metadata(
        output_path=output_path,
        manifest=cache_manifest,
        records=serialized_records,
        requested_subjects=subjects,
        selected_runs=selected_runs,
        include_music=include_music,
        dataset_dir=dataset_dir,
    )
    cache_metadata_path.write_text(json.dumps(_to_plain_python(cache_metadata), indent=2), encoding="utf-8")

    return {
        "manifest": cache_manifest,
        "run_records": run_records,
        "sober_target_path": str(sober_path),
        "perturbation_target_path": str(perturbation_path),
        "cache_metadata": cache_metadata,
    }
