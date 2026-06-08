from __future__ import annotations

import json
import math
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import BaseModel
from scipy.stats import ttest_rel

from .atlas import atlas_module_label_rows
from .constants import (
    DS003059_DATASET_ID,
    DS003059_DEFAULT_RUNS,
    DS003059_MUSIC_RUN,
    DS003059_SESSIONS,
    DS003059_VERSION,
    EMPIRICAL_CACHE_METADATA_FILENAME,
    EMPIRICAL_CACHE_SCHEMA_VERSION,
    MODULE_NAMES,
)
from .models import Ds003059RestManifest
from .runs import normalize_ds003059_runs
from .serialization import _to_plain_python


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
    if dataset_dir is not None and metadata.get("run_file_hash_status") == "available":
        if metadata.get("run_file_hashes") != current_inputs.get("run_file_hashes"):
            raise ValueError("Empirical cache raw run-file fingerprints changed; regenerate the empirical targets.")
    if metadata.get("cache_fingerprint") != current_fingerprint:
        raise ValueError("Empirical cache fingerprint mismatch; regenerate the empirical targets.")
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
