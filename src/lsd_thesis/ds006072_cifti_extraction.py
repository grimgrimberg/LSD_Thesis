from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import nibabel as nib
import numpy as np

from lsd_thesis.ds006072_payload_plan import REPO_ROOT

SCHEMA_VERSION = "ds006072_cifti_empirical_extraction.v1"
OUTPUT_RUN = "run-01"
SCHAEFER100_PARCELLATION_ID = "schaefer_100_yeo_7"
SCHAEFER100_MODULE_CONTRACT = "CIFTI fsLR cortex Schaefer100/Yeo7 parcel external validation"
SCHAEFER100_LABEL_RELATIVE_PATHS = {
    "left": Path("results/cortical_maps/neuromaps_annotations/schaefer100_from_mni_space-fsLR_den-32k_hemi-L_label.gii"),
    "right": Path("results/cortical_maps/neuromaps_annotations/schaefer100_from_mni_space-fsLR_den-32k_hemi-R_label.gii"),
}
MODULE_NAMES = (
    "cortex_left",
    "cortex_right",
    "thalamus",
    "striatal_basal_ganglia",
    "limbic_medial_temporal",
    "cerebellum",
    "brain_stem",
    "ventral_diencephalon",
)
RESAMPLING_RULE = "linear_resample_each_condition_to_within_subject_minimum_timepoint_count"
CONDITION_TO_SESSION = {
    "active_control_mtp": "ses-PLCB",
    "psilocybin": "ses-LSD",
}
STRUCTURE_TO_MODULE = {
    "CIFTI_STRUCTURE_CORTEX_LEFT": "cortex_left",
    "CIFTI_STRUCTURE_CORTEX_RIGHT": "cortex_right",
    "CIFTI_STRUCTURE_THALAMUS_LEFT": "thalamus",
    "CIFTI_STRUCTURE_THALAMUS_RIGHT": "thalamus",
    "CIFTI_STRUCTURE_ACCUMBENS_LEFT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_ACCUMBENS_RIGHT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_CAUDATE_LEFT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_CAUDATE_RIGHT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_PALLIDUM_LEFT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_PALLIDUM_RIGHT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_PUTAMEN_LEFT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_PUTAMEN_RIGHT": "striatal_basal_ganglia",
    "CIFTI_STRUCTURE_AMYGDALA_LEFT": "limbic_medial_temporal",
    "CIFTI_STRUCTURE_AMYGDALA_RIGHT": "limbic_medial_temporal",
    "CIFTI_STRUCTURE_HIPPOCAMPUS_LEFT": "limbic_medial_temporal",
    "CIFTI_STRUCTURE_HIPPOCAMPUS_RIGHT": "limbic_medial_temporal",
    "CIFTI_STRUCTURE_CEREBELLUM_LEFT": "cerebellum",
    "CIFTI_STRUCTURE_CEREBELLUM_RIGHT": "cerebellum",
    "CIFTI_STRUCTURE_BRAIN_STEM": "brain_stem",
    "CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_LEFT": "ventral_diencephalon",
    "CIFTI_STRUCTURE_DIENCEPHALON_VENTRAL_RIGHT": "ventral_diencephalon",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _rel(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists() or not path.is_file():
        return None
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Expected JSON object in {path}, got {type(raw).__name__}.")
    return raw


def _zscore_columns(values: np.ndarray) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    mean = np.mean(array, axis=0, keepdims=True)
    std = np.std(array, axis=0, keepdims=True)
    std = np.where(std > 1e-8, std, 1.0)
    return cast(np.ndarray, (array - mean) / std)


def _resample_vector(values: np.ndarray, point_count: int) -> np.ndarray:
    vector = np.asarray(values, dtype=float)
    if len(vector) == point_count:
        return cast(np.ndarray, vector.copy())
    positions = np.linspace(0, len(vector) - 1, point_count)
    return cast(np.ndarray, np.interp(positions, np.arange(len(vector)), vector).astype(float))


def _resample_matrix(values: np.ndarray, point_count: int) -> np.ndarray:
    matrix = np.asarray(values, dtype=float)
    if matrix.shape[0] == point_count:
        return matrix.copy()
    return np.stack([_resample_vector(matrix[:, column], point_count) for column in range(matrix.shape[1])], axis=1)


def _slice_width(slc: slice, axis_size: int) -> int:
    start = 0 if slc.start is None else int(slc.start)
    stop = axis_size if slc.stop is None else int(slc.stop)
    return max(stop - start, 0)


def _weighted_mean_for_slices(data: np.ndarray, slices: list[slice]) -> np.ndarray:
    axis_size = int(data.shape[1])
    weighted_sum = np.zeros(data.shape[0], dtype=float)
    total_width = 0
    for slc in slices:
        width = _slice_width(slc, axis_size)
        if width <= 0:
            continue
        weighted_sum += np.mean(data[:, slc], axis=1) * float(width)
        total_width += width
    if total_width <= 0:
        return np.zeros(data.shape[0], dtype=float)
    return weighted_sum / float(total_width)


def _extract_structure_family_series_from_dense(
    data: np.ndarray,
    structure_slices: dict[str, list[slice]],
) -> np.ndarray:
    columns = []
    for module in MODULE_NAMES:
        slices = structure_slices.get(module, [])
        if not slices:
            columns.append(np.zeros(data.shape[0], dtype=float))
        else:
            columns.append(_weighted_mean_for_slices(data, slices))
    return _zscore_columns(np.stack(columns, axis=1))


def _load_surface_label_values(path: Path) -> np.ndarray:
    image = nib.load(str(path))
    darrays = getattr(image, "darrays", None)
    if not darrays:
        raise ValueError(f"Expected a GIFTI label file with one data array: {path}")
    return np.asarray(darrays[0].data, dtype=int)


def _load_schaefer100_module_names(repo_root: Path) -> tuple[str, ...]:
    overview_path = (
        repo_root
        / "results"
        / "stage_2"
        / "parcellations"
        / SCHAEFER100_PARCELLATION_ID
        / "empirical_viewer"
        / "group_overview.json"
    )
    if overview_path.exists():
        overview = _read_json(overview_path) or {}
        module_names = overview.get("module_names")
        if isinstance(module_names, list) and len(module_names) == 100 and all(isinstance(name, str) for name in module_names):
            return tuple(module_names)

    label_path = (
        repo_root
        / "results"
        / "stage_2"
        / "parcellations"
        / SCHAEFER100_PARCELLATION_ID
        / "parcellation_extraction_summary.json"
    )
    summary = _read_json(label_path) or {}
    atlas_metadata = summary.get("atlas_metadata", {}) if isinstance(summary.get("atlas_metadata"), dict) else {}
    labels_path = Path(str(atlas_metadata.get("labels_path") or ""))
    if labels_path.exists():
        labels: list[str] = []
        for line in labels_path.read_text(encoding="utf-8").splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                labels.append(parts[1])
        if len(labels) == 100:
            return tuple(labels)

    return tuple(f"Schaefer100_parcel_{index:03d}" for index in range(1, 101))


def _mean_parcel_series(
    data: np.ndarray,
    axis: Any,
    left_labels: np.ndarray,
    right_labels: np.ndarray,
) -> tuple[np.ndarray, dict[str, int], list[int]]:
    parcel_sum = np.zeros((data.shape[0], 100), dtype=np.float64)
    parcel_count = np.zeros(100, dtype=int)
    surface_label_by_structure = {
        "CIFTI_STRUCTURE_CORTEX_LEFT": left_labels,
        "CIFTI_STRUCTURE_CORTEX_RIGHT": right_labels,
    }
    for structure_name, structure_slice, brain_model in axis.iter_structures():
        labels = surface_label_by_structure.get(str(structure_name))
        if labels is None:
            continue
        vertices = np.asarray(brain_model.vertex, dtype=int)
        if vertices.size == 0:
            continue
        valid = (vertices >= 0) & (vertices < len(labels))
        if not np.any(valid):
            continue
        structure_data = np.asarray(data[:, structure_slice], dtype=np.float32)
        structure_labels = np.zeros(vertices.shape, dtype=int)
        structure_labels[valid] = labels[vertices[valid]]
        for parcel_index in range(1, 101):
            mask = structure_labels == parcel_index
            if not np.any(mask):
                continue
            parcel_sum[:, parcel_index - 1] += np.sum(structure_data[:, mask], axis=1)
            parcel_count[parcel_index - 1] += int(np.sum(mask))
    missing = [index + 1 for index, count in enumerate(parcel_count) if count <= 0]
    if missing:
        raise ValueError(f"Missing Schaefer100 surface vertices for parcels: {missing}")
    series = parcel_sum / parcel_count[np.newaxis, :]
    return series, {str(index + 1): int(count) for index, count in enumerate(parcel_count)}, missing


def extract_schaefer100_cortex_time_series(
    path: Path,
    *,
    repo_root: Path = REPO_ROOT,
) -> tuple[np.ndarray, dict[str, Any]]:
    label_paths = {hemi: repo_root / rel_path for hemi, rel_path in SCHAEFER100_LABEL_RELATIVE_PATHS.items()}
    missing_labels = [str(path) for path in label_paths.values() if not path.exists()]
    if missing_labels:
        raise FileNotFoundError(f"Missing Schaefer100 fsLR label files: {', '.join(missing_labels)}")
    image = nib.load(str(path))
    if not isinstance(image, nib.Cifti2Image):
        raise TypeError(f"Expected a CIFTI2 image for {path}.")
    if len(image.shape) != 2:
        raise ValueError(f"Expected dense CIFTI time series shaped [time, grayordinate], got {image.shape}.")
    axis = image.header.get_axis(1)
    left_labels = _load_surface_label_values(label_paths["left"])
    right_labels = _load_surface_label_values(label_paths["right"])
    data = np.asarray(image.get_fdata(dtype=np.float32), dtype=np.float32)
    parcel_series, vertex_counts, missing = _mean_parcel_series(data, axis, left_labels, right_labels)
    module_names = _load_schaefer100_module_names(repo_root)
    metadata = {
        "source_shape": list(image.shape),
        "parcellation_id": SCHAEFER100_PARCELLATION_ID,
        "module_contract": SCHAEFER100_MODULE_CONTRACT,
        "module_names": list(module_names),
        "surface_label_paths": {hemi: _rel(label_path, repo_root) for hemi, label_path in label_paths.items()},
        "parcel_vertex_counts": vertex_counts,
        "missing_parcels": missing,
        "standardization": "zscore_each_schaefer100_parcel_time_series_within_run",
    }
    return _zscore_columns(parcel_series), metadata


def extract_structure_family_time_series(path: Path) -> tuple[np.ndarray, dict[str, Any]]:
    image = nib.load(str(path))
    if not isinstance(image, nib.Cifti2Image):
        raise TypeError(f"Expected a CIFTI2 image for {path}.")
    if len(image.shape) != 2:
        raise ValueError(f"Expected dense CIFTI time series shaped [time, grayordinate], got {image.shape}.")
    axis = image.header.get_axis(1)
    structure_slices: dict[str, list[slice]] = {module: [] for module in MODULE_NAMES}
    structure_counts: dict[str, int] = {}
    for structure_name, structure_slice, brain_model in axis.iter_structures():
        module = STRUCTURE_TO_MODULE.get(str(structure_name))
        if module is None:
            continue
        structure_slices[module].append(structure_slice)
        structure_counts[str(structure_name)] = len(brain_model)
    missing_modules = [module for module in MODULE_NAMES if not structure_slices[module]]
    if missing_modules:
        raise ValueError(f"CIFTI file {path} is missing required structure families: {', '.join(missing_modules)}")
    data = np.asarray(image.get_fdata(dtype=np.float32), dtype=float)
    series = _extract_structure_family_series_from_dense(data, structure_slices)
    metadata = {
        "source_shape": list(image.shape),
        "structure_counts": structure_counts,
        "module_names": list(MODULE_NAMES),
        "standardization": "zscore_each_structure_family_time_series_within_run",
    }
    return series, metadata


def _group_selected_files(plan: dict[str, Any]) -> dict[str, dict[str, dict[str, Any]]]:
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for row in plan.get("selected_files", []):
        if not isinstance(row, dict):
            continue
        subject = str(row.get("subject") or "")
        condition = str(row.get("condition") or "")
        session = CONDITION_TO_SESSION.get(condition)
        if not subject or session is None:
            continue
        grouped.setdefault(subject, {})[session] = row
    return grouped


def _write_group_overview(viewer_root: Path, subjects: list[str], extraction_rows: list[dict[str, Any]]) -> None:
    payload = {
        "subjects": subjects,
        "runs": [OUTPUT_RUN],
        "default_subject": subjects[0] if subjects else None,
        "module_names": list(MODULE_NAMES),
        "conditions": {},
        "paired_subject_count": len(subjects),
        "delta_metrics": {},
        "delta_metrics_std": {},
        "gallery": [],
        "extraction_metadata": {
            "schema_version": SCHEMA_VERSION,
            "module_contract": "CIFTI brain-structure-family 8-module external stress test",
            "source": "OpenNeuro ds006072 processed rest CIFTI dtseries files",
            "rows": extraction_rows,
            "claim_guardrail": (
                "This uses CIFTI brain-structure families, not the original ds003059 Harvard-Oxford macro-module extraction. "
                "Treat it as an empirical external stress test until a surface/parcellation-matched extractor is added."
            ),
        },
    }
    (viewer_root / "group_overview.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_schaefer100_group_overview(
    viewer_root: Path,
    subjects: list[str],
    extraction_rows: list[dict[str, Any]],
    module_names: tuple[str, ...],
) -> None:
    payload = {
        "subjects": subjects,
        "runs": [OUTPUT_RUN],
        "default_subject": subjects[0] if subjects else None,
        "module_names": list(module_names),
        "conditions": {},
        "paired_subject_count": len(subjects),
        "delta_metrics": {},
        "delta_metrics_std": {},
        "gallery": [],
        "extraction_metadata": {
            "schema_version": SCHEMA_VERSION,
            "parcellation_id": SCHAEFER100_PARCELLATION_ID,
            "module_contract": SCHAEFER100_MODULE_CONTRACT,
            "source": "OpenNeuro ds006072 processed rest CIFTI dtseries files",
            "rows": extraction_rows,
            "claim_guardrail": (
                "This uses ds006072 CIFTI cortical grayordinates projected to the same "
                "Schaefer100/Yeo7 parcel contract used by the ds003059 sensitivity layer. "
                "It is still a small-subject external stress test, not a population replication."
            ),
        },
    }
    (viewer_root / "group_overview.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_ds006072_cifti_empirical_viewer(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    plan_path = repo_root / "results" / "psilocybin_ds006072" / "minimum_payload_plan.json"
    plan = _read_json(plan_path)
    if not plan:
        raise FileNotFoundError(f"Missing ds006072 minimum payload plan: {plan_path}")
    grouped = _group_selected_files(plan)
    viewer_root = repo_root / "results" / "psilocybin_ds006072" / "empirical_viewer"
    subject_views_dir = viewer_root / "subject_views"
    subject_views_dir.mkdir(parents=True, exist_ok=True)
    subjects_written: list[str] = []
    extraction_rows: list[dict[str, Any]] = []
    for subject, sessions in sorted(grouped.items()):
        if not all(session in sessions for session in CONDITION_TO_SESSION.values()):
            continue
        conditions: dict[str, Any] = {}
        extracted: dict[str, tuple[np.ndarray, dict[str, Any], dict[str, Any]]] = {}
        for session, row in sorted(sessions.items()):
            local_path = repo_root / str(row["local_path"])
            if not local_path.exists():
                raise FileNotFoundError(f"Selected ds006072 payload is missing: {local_path}")
            time_series, metadata = extract_structure_family_time_series(local_path)
            extracted[session] = (time_series, metadata, row)

        paired_timepoint_count = min(int(series.shape[0]) for series, _, _ in extracted.values())
        for session, (time_series, metadata, row) in sorted(extracted.items()):
            paired_series = _resample_matrix(time_series, paired_timepoint_count)
            conditions[session] = {
                "module_time_series": paired_series.tolist(),
                "source_path": _rel(repo_root / str(row["local_path"]), repo_root),
                "source_condition": row.get("condition"),
                "source_session_suffix": row.get("session_suffix"),
                "extraction_metadata": {
                    **metadata,
                    "original_timepoint_count": int(time_series.shape[0]),
                    "paired_timepoint_count": paired_timepoint_count,
                    "resampling_rule": RESAMPLING_RULE,
                },
            }
            extraction_rows.append(
                {
                    "subject": subject,
                    "session": session,
                    "condition": row.get("condition"),
                    "source_path": _rel(repo_root / str(row["local_path"]), repo_root),
                    "source_shape": metadata["source_shape"],
                    "paired_timepoint_count": paired_timepoint_count,
                }
            )
        detail = {
            "subject": subject,
            "run": OUTPUT_RUN,
            "conditions": conditions,
            "extraction_contract": "ds006072_cifti_structure_family_external_stress_test",
        }
        (subject_views_dir / f"{subject}_{OUTPUT_RUN}.json").write_text(json.dumps(detail, indent=2), encoding="utf-8")
        subjects_written.append(subject)
    _write_group_overview(viewer_root, subjects_written, extraction_rows)
    return {
        "subjects_written": subjects_written,
        "subject_view_count": len(subjects_written),
        "condition_file_count": len(extraction_rows),
        "viewer_root": _rel(viewer_root, repo_root),
        "subject_views_dir": _rel(subject_views_dir, repo_root),
        "extraction_rows": extraction_rows,
    }


def write_ds006072_schaefer100_empirical_viewer(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    plan_path = repo_root / "results" / "psilocybin_ds006072" / "minimum_payload_plan.json"
    plan = _read_json(plan_path)
    if not plan:
        raise FileNotFoundError(f"Missing ds006072 minimum payload plan: {plan_path}")
    grouped = _group_selected_files(plan)
    viewer_root = (
        repo_root
        / "results"
        / "psilocybin_ds006072"
        / "parcellations"
        / SCHAEFER100_PARCELLATION_ID
        / "empirical_viewer"
    )
    subject_views_dir = viewer_root / "subject_views"
    subject_views_dir.mkdir(parents=True, exist_ok=True)
    module_names = _load_schaefer100_module_names(repo_root)
    subjects_written: list[str] = []
    extraction_rows: list[dict[str, Any]] = []
    for subject, sessions in sorted(grouped.items()):
        if not all(session in sessions for session in CONDITION_TO_SESSION.values()):
            continue
        conditions: dict[str, Any] = {}
        extracted: dict[str, tuple[np.ndarray, dict[str, Any], dict[str, Any]]] = {}
        for session, row in sorted(sessions.items()):
            local_path = repo_root / str(row["local_path"])
            if not local_path.exists():
                raise FileNotFoundError(f"Selected ds006072 payload is missing: {local_path}")
            time_series, metadata = extract_schaefer100_cortex_time_series(local_path, repo_root=repo_root)
            extracted[session] = (time_series, metadata, row)

        paired_timepoint_count = min(int(series.shape[0]) for series, _, _ in extracted.values())
        for session, (time_series, metadata, row) in sorted(extracted.items()):
            paired_series = _resample_matrix(time_series, paired_timepoint_count)
            conditions[session] = {
                "module_time_series": paired_series.tolist(),
                "source_path": _rel(repo_root / str(row["local_path"]), repo_root),
                "source_condition": row.get("condition"),
                "source_session_suffix": row.get("session_suffix"),
                "extraction_metadata": {
                    **metadata,
                    "original_timepoint_count": int(time_series.shape[0]),
                    "paired_timepoint_count": paired_timepoint_count,
                    "resampling_rule": RESAMPLING_RULE,
                },
            }
            extraction_rows.append(
                {
                    "subject": subject,
                    "session": session,
                    "condition": row.get("condition"),
                    "source_path": _rel(repo_root / str(row["local_path"]), repo_root),
                    "source_shape": metadata["source_shape"],
                    "paired_timepoint_count": paired_timepoint_count,
                    "parcellation_id": SCHAEFER100_PARCELLATION_ID,
                }
            )
        detail = {
            "subject": subject,
            "run": OUTPUT_RUN,
            "conditions": conditions,
            "extraction_contract": SCHAEFER100_MODULE_CONTRACT,
            "parcellation_id": SCHAEFER100_PARCELLATION_ID,
        }
        (subject_views_dir / f"{subject}_{OUTPUT_RUN}.json").write_text(json.dumps(detail, indent=2), encoding="utf-8")
        subjects_written.append(subject)
    _write_schaefer100_group_overview(viewer_root, subjects_written, extraction_rows, module_names)
    return {
        "subjects_written": subjects_written,
        "subject_view_count": len(subjects_written),
        "condition_file_count": len(extraction_rows),
        "viewer_root": _rel(viewer_root, repo_root),
        "subject_views_dir": _rel(subject_views_dir, repo_root),
        "module_contract": SCHAEFER100_MODULE_CONTRACT,
        "parcellation_id": SCHAEFER100_PARCELLATION_ID,
        "extraction_rows": extraction_rows,
    }


def build_ds006072_cifti_extraction_status(repo_root: Path = REPO_ROOT) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    plan_path = repo_root / "results" / "psilocybin_ds006072" / "minimum_payload_plan.json"
    viewer_root = repo_root / "results" / "psilocybin_ds006072" / "empirical_viewer"
    subject_views_dir = viewer_root / "subject_views"
    schaefer100_viewer_root = (
        repo_root
        / "results"
        / "psilocybin_ds006072"
        / "parcellations"
        / SCHAEFER100_PARCELLATION_ID
        / "empirical_viewer"
    )
    schaefer100_subject_views_dir = schaefer100_viewer_root / "subject_views"
    plan = _read_json(plan_path) or {}
    subject_view_count = len(list(subject_views_dir.glob("*.json"))) if subject_views_dir.exists() else 0
    schaefer100_subject_view_count = (
        len(list(schaefer100_subject_views_dir.glob("*.json"))) if schaefer100_subject_views_dir.exists() else 0
    )
    minimum_subjects = int(plan.get("minimum_subjects_required") or 3)
    payloads_ready = bool(plan.get("minimum_payloads_local_ready"))
    ready = subject_view_count >= minimum_subjects
    schaefer100_ready = schaefer100_subject_view_count >= minimum_subjects
    if ready:
        analysis_status = (
            "implemented_ds006072_schaefer100_parcellation_empirical_viewer"
            if schaefer100_ready
            else "implemented_ds006072_cifti_structure_family_empirical_viewer"
        )
        blocker = ""
    elif payloads_ready:
        analysis_status = "payloads_local_ready_missing_cifti_empirical_viewer"
        blocker = "Selected ds006072 CIFTIs are local, but empirical-viewer records have not been extracted yet."
    elif plan.get("minimum_payload_plan_ready"):
        analysis_status = "minimum_payload_plan_ready_missing_local_payloads"
        blocker = "Minimum selected ds006072 CIFTIs are not local yet."
    else:
        analysis_status = "blocked_missing_minimum_payload_plan"
        blocker = "No minimum ds006072 payload plan is available."
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at_utc": _now(),
        "analysis_status": analysis_status,
        "cifti_empirical_viewer_ready": ready,
        "schaefer100_empirical_viewer_ready": schaefer100_ready,
        "stronger_external_validation_ready": schaefer100_ready,
        "minimum_subjects_required": minimum_subjects,
        "minimum_payloads_local_ready": payloads_ready,
        "subject_view_count": subject_view_count,
        "schaefer100_subject_view_count": schaefer100_subject_view_count,
        "viewer_root": _rel(viewer_root, repo_root),
        "subject_views_dir": _rel(subject_views_dir, repo_root),
        "schaefer100_viewer_root": _rel(schaefer100_viewer_root, repo_root),
        "schaefer100_subject_views_dir": _rel(schaefer100_subject_views_dir, repo_root),
        "module_names": list(MODULE_NAMES),
        "module_contract": "CIFTI brain-structure-family 8-module external stress test",
        "schaefer100_module_contract": SCHAEFER100_MODULE_CONTRACT,
        "schaefer100_parcellation_id": SCHAEFER100_PARCELLATION_ID,
        "resampling_rule": RESAMPLING_RULE,
        "blocker": blocker,
        "next_commands": [
            ".\\.venv\\Scripts\\python.exe scripts\\build_ds006072_payload_plan.py --execute",
            ".\\.venv\\Scripts\\python.exe scripts\\build_ds006072_cifti_empirical_viewer.py --execute",
            ".\\.venv\\Scripts\\python.exe scripts\\build_ds006072_comparable_validation.py",
        ],
        "claim_status": (
            "schaefer100_empirical_viewer_ready_for_unchanged_scoring"
            if schaefer100_ready
            else "empirical_viewer_ready_for_unchanged_scoring"
            if ready
            else "local_payload_ready_needs_extraction"
            if payloads_ready
            else "not_ready_for_external_extraction"
        ),
        "claim_guardrail": (
            "This is real ds006072 CIFTI extraction into an empirical viewer, but it uses broad CIFTI structure families. "
            "It is stronger than manifest readiness and weaker than a surface/parcellation-matched replication unless "
            "schaefer100_empirical_viewer_ready is true."
        ),
    }


def _markdown(status: dict[str, Any]) -> str:
    lines = [
        "# ds006072 CIFTI Empirical Extraction Status",
        "",
        status["claim_guardrail"],
        "",
        f"- Status: `{status['analysis_status']}`",
        f"- Claim status: `{status['claim_status']}`",
        f"- Minimum subjects required: `{status['minimum_subjects_required']}`",
        f"- Subject-view count: `{status['subject_view_count']}`",
        f"- Module contract: `{status['module_contract']}`",
        "",
        "## Modules",
        "",
        ", ".join(f"`{module}`" for module in status["module_names"]),
        "",
    ]
    if status["blocker"]:
        lines.extend(["## Blocker", "", status["blocker"], ""])
    lines.extend(
        [
            "## Stronger Schaefer100 Layer",
            "",
            f"- Schaefer100 ready: `{str(status['schaefer100_empirical_viewer_ready']).lower()}`",
            f"- Schaefer100 subject-view count: `{status['schaefer100_subject_view_count']}`",
            f"- Schaefer100 viewer: `{status['schaefer100_viewer_root']}`",
            "",
            "## Next commands",
            "",
        ]
    )
    lines.extend(f"- `{command}`" for command in status["next_commands"])
    return "\n".join(lines) + "\n"


def write_ds006072_cifti_extraction_status(
    repo_root: Path = REPO_ROOT,
    output_dir: Path | None = None,
    *,
    execute: bool = False,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output_dir = output_dir or repo_root / "results" / "psilocybin_ds006072"
    output_dir.mkdir(parents=True, exist_ok=True)
    extraction_result = None
    schaefer100_extraction_result = None
    if execute:
        extraction_result = write_ds006072_cifti_empirical_viewer(repo_root)
        schaefer100_extraction_result = write_ds006072_schaefer100_empirical_viewer(repo_root)
    status = build_ds006072_cifti_extraction_status(repo_root)
    status["execute_requested"] = bool(execute)
    status["extraction_result"] = extraction_result
    status["schaefer100_extraction_result"] = schaefer100_extraction_result
    status_path = output_dir / "cifti_empirical_extraction_status.json"
    report_path = output_dir / "cifti_empirical_extraction_status.md"
    status_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
    report_path.write_text(_markdown(status), encoding="utf-8")
    status["source_path"] = _rel(status_path, repo_root)
    status["report_path"] = _rel(report_path, repo_root)
    return status
